from flask import Flask, jsonify, request, render_template
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)

DB_CONFIG = {
    "dbname":   os.environ.get("DB_NAME", "autoselect"),
    "user":     os.environ["DB_USER"],
    "password": os.environ.get("DB_PASSWORD", ""),
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", "5432")),
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def query(sql, params=None):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

def execute(sql, params=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()

# ── Page routes ────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ── Customer API ───────────────────────────────────────────────

@app.route("/api/vehicles")
def get_vehicles():
    fuel   = request.args.get("fuel")
    budget = request.args.get("budget")
    brand  = request.args.get("brand")
    body   = request.args.get("body")

    conditions = ["1=1"]
    params = []

    if fuel:
        conditions.append("v.fuel_type = %s")
        params.append(fuel)
    if budget:
        conditions.append("v.price <= %s")
        params.append(float(budget))
    if brand:
        conditions.append("v.brand ILIKE %s")
        params.append(f"%{brand}%")
    if body:
        conditions.append("v.body_style = %s")
        params.append(body)

    sql = f"""
        SELECT v.vehicle_id, v.brand, v.model, v.year, v.price,
               v.fuel_type, v.body_style, v.engine_type,
               COUNT(DISTINCT i.dealership_id) AS dealership_count,
               SUM(i.stock_quantity) AS total_stock
        FROM Vehicle v
        LEFT JOIN Inventory i ON v.vehicle_id = i.vehicle_id
            AND i.availability_status = 'available'
        WHERE {' AND '.join(conditions)}
        GROUP BY v.vehicle_id
        ORDER BY v.brand, v.price
    """
    return jsonify(query(sql, params))

@app.route("/api/vehicles/<int:vid>/dealerships")
def vehicle_dealerships(vid):
    sql = """
        SELECT d.dealership_name, d.location, d.phone_number,
               i.stock_quantity, i.price AS dealer_price,
               i.availability_status
        FROM Inventory i
        JOIN Dealership d ON i.dealership_id = d.dealership_id
        WHERE i.vehicle_id = %s
        ORDER BY i.price
    """
    return jsonify(query(sql, (vid,)))

@app.route("/api/vehicles/<int:vid>/financing")
def vehicle_financing(vid):
    sql = """
        SELECT d.dealership_name, d.location,
               f.interest_rate, f.loan_term_months, f.min_down_payment
        FROM Vehicle v
        JOIN Inventory  i ON v.vehicle_id    = i.vehicle_id
        JOIN Dealership d ON i.dealership_id = d.dealership_id
        JOIN Financing  f ON d.dealership_id = f.dealership_id
        WHERE v.vehicle_id = %s
          AND i.availability_status = 'available'
        ORDER BY f.interest_rate
    """
    return jsonify(query(sql, (vid,)))

@app.route("/api/dealerships")
def get_dealerships():
    return jsonify(query("SELECT * FROM Dealership ORDER BY dealership_name"))

@app.route("/api/dealerships/<int:did>/inventory")
def dealership_inventory(did):
    sql = """
        SELECT v.vehicle_id, v.brand, v.model, v.year, v.fuel_type,
               v.body_style, i.stock_quantity, i.price, i.availability_status
        FROM Inventory i
        JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
        WHERE i.dealership_id = %s
        ORDER BY i.availability_status, i.price
    """
    return jsonify(query(sql, (did,)))

@app.route("/api/stats/fuel")
def stats_fuel():
    sql = """
        SELECT v.fuel_type,
               COUNT(DISTINCT v.vehicle_id) AS unique_models,
               COALESCE(SUM(i.stock_quantity), 0) AS total_stock
        FROM Vehicle v
        LEFT JOIN Inventory i ON v.vehicle_id = i.vehicle_id
            AND i.availability_status = 'available'
        GROUP BY v.fuel_type
        ORDER BY total_stock DESC
    """
    return jsonify(query(sql))

@app.route("/api/stats/ev_leaders")
def ev_leaders():
    sql = """
        SELECT d.dealership_name, d.location,
               COUNT(DISTINCT v.vehicle_id) AS ev_models
        FROM Inventory i
        JOIN Vehicle    v ON i.vehicle_id    = v.vehicle_id
        JOIN Dealership d ON i.dealership_id = d.dealership_id
        WHERE v.fuel_type = 'Electric'
          AND i.availability_status = 'available'
        GROUP BY d.dealership_id, d.dealership_name, d.location
        HAVING COUNT(DISTINCT v.vehicle_id) >= 2
        ORDER BY ev_models DESC
    """
    return jsonify(query(sql))

@app.route("/api/stats/summary")
def stats_summary():
    rows = query("""
        SELECT
          (SELECT COUNT(*) FROM Vehicle) AS total_vehicles,
          (SELECT COUNT(*) FROM Dealership) AS total_dealerships,
          (SELECT COALESCE(SUM(stock_quantity),0) FROM Inventory WHERE availability_status='available') AS total_stock,
          (SELECT COUNT(*) FROM Vehicle WHERE fuel_type='Electric') AS electric_models,
          (SELECT ROUND(AVG(price)::numeric,0) FROM Vehicle) AS avg_price,
          (SELECT MIN(price) FROM Vehicle) AS min_price,
          (SELECT MAX(price) FROM Vehicle) AS max_price
    """)
    return jsonify(rows[0] if rows else {})

# ── Admin API ──────────────────────────────────────────────────

@app.route("/api/admin/inventory", methods=["POST"])
def admin_add_inventory():
    d = request.json
    sql = """
        INSERT INTO Inventory (vehicle_id, dealership_id, stock_quantity, price, availability_status)
        VALUES (%s, %s, %s, %s, 'available')
        ON CONFLICT (vehicle_id, dealership_id)
        DO UPDATE SET stock_quantity = EXCLUDED.stock_quantity,
                      price = EXCLUDED.price,
                      availability_status = 'available'
    """
    execute(sql, (d["vehicle_id"], d["dealership_id"], d["stock_quantity"], d["price"]))
    return jsonify({"success": True})

@app.route("/api/admin/inventory", methods=["PATCH"])
def admin_update_price():
    d = request.json
    execute(
        "UPDATE Inventory SET price = %s, stock_quantity = %s WHERE vehicle_id = %s AND dealership_id = %s",
        (d["price"], d["stock_quantity"], d["vehicle_id"], d["dealership_id"])
    )
    return jsonify({"success": True})

@app.route("/api/admin/inventory", methods=["DELETE"])
def admin_remove_inventory():
    d = request.json
    execute(
        "UPDATE Inventory SET availability_status = 'discontinued' WHERE vehicle_id = %s AND dealership_id = %s",
        (d["vehicle_id"], d["dealership_id"])
    )
    return jsonify({"success": True})

@app.route("/api/admin/vehicles", methods=["POST"])
def admin_add_vehicle():
    d = request.json
    sql = """
        INSERT INTO Vehicle (brand, model, year, price, fuel_type, engine_type, body_style)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING vehicle_id
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (d["brand"], d["model"], d["year"], d["price"],
                              d["fuel_type"], d.get("engine_type"), d.get("body_style")))
            vid = cur.fetchone()[0]
        conn.commit()
    return jsonify({"success": True, "vehicle_id": vid})

if __name__ == "__main__":
    app.run(debug=True, port=5050)
