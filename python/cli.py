import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

# ── Database connection ────────────────────────────────────────
DB_CONFIG = {
    "dbname":   os.environ.get("DB_NAME", "autoselect"),
    "user":     os.environ["DB_USER"],
    "password": os.environ.get("DB_PASSWORD", ""),
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", "5432")),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_query(sql, params=None):
    """Execute a SELECT and return rows as a list of dicts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def run_write(sql, params=None):
    """Execute INSERT / UPDATE / DELETE."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()

# ── Display helpers ────────────────────────────────────────────
def print_table(rows):
    if not rows:
        print("  (no results)\n")
        return
    headers = list(rows[0].keys())
    widths  = {h: max(len(str(h)), max(len(str(r[h])) for r in rows)) for h in headers}
    sep = "+-" + "-+-".join("-" * widths[h] for h in headers) + "-+"
    print(sep)
    print("| " + " | ".join(str(h).ljust(widths[h]) for h in headers) + " |")
    print(sep)
    for row in rows:
        print("| " + " | ".join(str(row[h]).ljust(widths[h]) for h in headers) + " |")
    print(sep)
    print(f"  {len(rows)} row(s)\n")

def prompt(msg):
    return input(f"  {msg}: ").strip()

# ── Query functions ────────────────────────────────────────────

def search_by_fuel_and_budget():
    """E1 — Search vehicles by fuel type and max budget."""
    fuel   = prompt("Fuel type (Gas / Hybrid / Electric / Diesel)")
    budget = prompt("Max budget ($)")
    sql = """
        SELECT brand, model, year, price, fuel_type, body_style
        FROM Vehicle
        WHERE LOWER(fuel_type) = LOWER(%s) AND price <= %s
        ORDER BY price
    """
    print_table(run_query(sql, (fuel, budget)))

def search_by_brand():
    """E2 — Search all vehicles by brand."""
    brand = prompt("Brand (e.g. Toyota, Tesla, Ford)")
    sql = """
        SELECT brand, model, year, price, fuel_type, body_style
        FROM Vehicle
        WHERE brand ILIKE %s
        ORDER BY price
    """
    print_table(run_query(sql, (f"%{brand}%",)))

def available_at_dealership():
    """M1 — Show vehicles in stock at a specific dealership."""
    print("  Available dealerships:")
    dealers = run_query("SELECT dealership_id, dealership_name, location FROM Dealership ORDER BY dealership_id")
    for d in dealers:
        print(f"    [{d['dealership_id']}] {d['dealership_name']} — {d['location']}")
    did = prompt("Enter dealership ID")
    sql = """
        SELECT v.brand, v.model, v.year, v.fuel_type,
               i.stock_quantity, i.price, i.availability_status
        FROM Inventory i
        JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
        WHERE i.dealership_id = %s
          AND i.availability_status = 'available'
        ORDER BY i.price
    """
    print_table(run_query(sql, (did,)))

def electric_vehicles_in_stock():
    """M2 — All electric vehicles available at any dealership."""
    sql = """
        SELECT v.brand, v.model, v.year,
               d.dealership_name, d.location,
               i.stock_quantity, i.price AS dealer_price
        FROM Inventory i
        JOIN Vehicle    v ON i.vehicle_id    = v.vehicle_id
        JOIN Dealership d ON i.dealership_id = d.dealership_id
        WHERE v.fuel_type = 'Electric'
          AND i.availability_status = 'available'
        ORDER BY i.price
    """
    print_table(run_query(sql))

def financing_options():
    """M3 — Financing options available at dealerships that stock a vehicle."""
    brand = prompt("Brand")
    model = prompt("Model")
    sql = """
        SELECT d.dealership_name, d.location,
               f.interest_rate, f.loan_term_months, f.min_down_payment
        FROM Vehicle    v
        JOIN Inventory  i ON v.vehicle_id    = i.vehicle_id
        JOIN Dealership d ON i.dealership_id = d.dealership_id
        JOIN Financing  f ON d.dealership_id = f.dealership_id
        WHERE v.brand ILIKE %s AND v.model ILIKE %s
          AND i.availability_status = 'available'
        ORDER BY f.interest_rate
    """
    print_table(run_query(sql, (f"%{brand}%", f"%{model}%")))

def stock_by_fuel_type():
    """M4 — Total stock count grouped by fuel type."""
    sql = """
        SELECT v.fuel_type,
               COUNT(DISTINCT v.vehicle_id) AS unique_models,
               SUM(i.stock_quantity)        AS total_stock
        FROM Inventory i
        JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
        WHERE i.availability_status = 'available'
        GROUP BY v.fuel_type
        ORDER BY total_stock DESC
    """
    print_table(run_query(sql))

def cheapest_per_brand():
    """H1 — Cheapest and most expensive vehicle per brand."""
    sql = """
        SELECT brand, model, year, price, fuel_type,
               MIN(price) OVER (PARTITION BY brand) AS brand_min,
               MAX(price) OVER (PARTITION BY brand) AS brand_max
        FROM Vehicle
        ORDER BY brand, price
    """
    print_table(run_query(sql))

def ev_dealership_leaders():
    """H2 — Dealerships stocking 2+ distinct EV models."""
    sql = """
        SELECT d.dealership_name, d.location,
               COUNT(DISTINCT v.vehicle_id) AS ev_models
        FROM Inventory  i
        JOIN Vehicle    v ON i.vehicle_id    = v.vehicle_id
        JOIN Dealership d ON i.dealership_id = d.dealership_id
        WHERE v.fuel_type = 'Electric'
          AND i.availability_status = 'available'
        GROUP BY d.dealership_id, d.dealership_name, d.location
        HAVING COUNT(DISTINCT v.vehicle_id) >= 2
        ORDER BY ev_models DESC
    """
    print_table(run_query(sql))

def add_inventory():
    """Admin — Add or update a vehicle in a dealership's inventory."""
    print("  Available vehicles:")
    vehicles = run_query("SELECT vehicle_id, brand, model, year FROM Vehicle ORDER BY brand, model")
    for v in vehicles:
        print(f"    [{v['vehicle_id']}] {v['brand']} {v['model']} {v['year']}")
    vid = prompt("Vehicle ID")

    print("\n  Available dealerships:")
    dealers = run_query("SELECT dealership_id, dealership_name FROM Dealership ORDER BY dealership_id")
    for d in dealers:
        print(f"    [{d['dealership_id']}] {d['dealership_name']}")
    did   = prompt("Dealership ID")
    qty   = prompt("Stock quantity")
    price = prompt("Price ($)")

    sql = """
        INSERT INTO Inventory (vehicle_id, dealership_id, stock_quantity, price, availability_status)
        VALUES (%s, %s, %s, %s, 'available')
        ON CONFLICT (vehicle_id, dealership_id)
        DO UPDATE SET stock_quantity = EXCLUDED.stock_quantity,
                      price = EXCLUDED.price,
                      availability_status = 'available'
    """
    run_write(sql, (vid, did, qty, price))
    print("  Inventory updated.\n")

def update_price():
    """Admin — Update the price of a vehicle at a dealership."""
    vid   = prompt("Vehicle ID")
    did   = prompt("Dealership ID")
    price = prompt("New price ($)")
    run_write(
        "UPDATE Inventory SET price = %s WHERE vehicle_id = %s AND dealership_id = %s",
        (price, vid, did)
    )
    print("  Price updated.\n")

# ── Menu ───────────────────────────────────────────────────────
MENU = [
    ("Search vehicles by fuel type + budget",       search_by_fuel_and_budget),
    ("Search vehicles by brand",                    search_by_brand),
    ("View inventory at a dealership",               available_at_dealership),
    ("View all electric vehicles in stock",          electric_vehicles_in_stock),
    ("View financing options for a vehicle",         financing_options),
    ("Stock summary by fuel type",                   stock_by_fuel_type),
    ("Cheapest + most expensive per brand",          cheapest_per_brand),
    ("Dealerships with 2+ EV models in stock",       ev_dealership_leaders),
    ("--- ADMIN: Add / update inventory",            add_inventory),
    ("--- ADMIN: Update vehicle price",              update_price),
]

def main():
    print("\n╔══════════════════════════════════════╗")
    print("║   AutoSelect — Car Recommendation    ║")
    print("║   & Inventory Management System      ║")
    print("╚══════════════════════════════════════╝\n")

    while True:
        print("Main Menu:")
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  [{i:2}] {label}")
        print("  [ 0] Exit\n")

        choice = prompt("Select an option")
        if choice == "0":
            print("\n  Goodbye.\n")
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MENU):
                print()
                MENU[idx][1]()
            else:
                print("  Invalid choice.\n")
        except ValueError:
            print("  Please enter a number.\n")
        except psycopg2.Error as e:
            print(f"  Database error: {e}\n")

if __name__ == "__main__":
    main()
