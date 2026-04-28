"""
AutoSelect — Demo Script
CSDS 341 Final Project

Runs a scripted walkthrough of all key system features.
No typing required during the demo — just run and narrate.

Usage:
    python demo.py            # full demo, pauses between steps
    python demo.py --fast     # no pauses (for practice timing)
    python demo.py --step 3   # jump to a specific step
"""

import argparse
import time
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname":   "autoselect",
    "user":     "dhoopshikhabasgeet",
    "password": "",           # set your password here
    "host":     "localhost",
    "port":     5432,
}

FAST = False  # set by --fast flag

# ── Helpers ────────────────────────────────────────────────────

def run_query(sql, params=None):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def run_write(sql, params=None):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()

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

def header(step, title, subtitle=""):
    print("\n" + "═" * 60)
    print(f"  STEP {step}: {title}")
    if subtitle:
        print(f"  {subtitle}")
    print("═" * 60 + "\n")

def say(text):
    """Print narration in a distinct style."""
    print(f"  >> {text}\n")

def pause(msg="Press Enter to continue..."):
    if not FAST:
        input(f"  [ {msg} ]\n")
    else:
        time.sleep(0.4)

def show_sql(sql):
    """Print the SQL being run, trimmed and indented."""
    lines = [l for l in sql.strip().splitlines() if l.strip()]
    print("  SQL:")
    for line in lines:
        print(f"    {line.strip()}")
    print()

# ── Demo steps ─────────────────────────────────────────────────

def step1_connection():
    header(1, "Database connection", "Verifying AutoSelect is live")
    say("First, let's confirm the database is connected and all 6 tables exist.")

    rows = run_query("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns c
                WHERE c.table_name = t.table_name
                  AND c.table_schema = 'public') AS columns
        FROM information_schema.tables t
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    print_table(rows)

    counts = run_query("""
        SELECT 'Vehicle'      AS table_name, COUNT(*) AS rows FROM Vehicle
        UNION ALL
        SELECT 'Dealership',                 COUNT(*)         FROM Dealership
        UNION ALL
        SELECT 'Inventory',                  COUNT(*)         FROM Inventory
        UNION ALL
        SELECT 'Financing',                  COUNT(*)         FROM Financing
        UNION ALL
        SELECT 'Customer',                   COUNT(*)         FROM Customer
        UNION ALL
        SELECT 'SearchHistory',              COUNT(*)         FROM SearchHistory
        ORDER BY table_name
    """)
    say("Row counts across all tables:")
    print_table(counts)
    pause()

def step2_easy_query():
    header(2, "Easy query — E1", "Customer searches for electric vehicles under $45,000")
    say("Sarah has a $45k budget and wants an electric vehicle. Single-table SELECT with WHERE and ORDER BY.")

    sql = """
        SELECT brand, model, year, price, body_style
        FROM   Vehicle
        WHERE  fuel_type = 'Electric'
          AND  price < 45000
        ORDER  BY price ASC
    """
    show_sql(sql)
    print_table(run_query(sql))
    pause()

def step3_medium_query():
    header(3, "Medium query — M2", "All EVs in stock across all dealerships (3-table JOIN)")
    say("Now we join Vehicle + Inventory + Dealership to show WHERE each EV is physically available and at what dealer price.")

    sql = """
        SELECT v.brand, v.model, v.year,
               d.dealership_name, d.location,
               i.stock_quantity, i.price AS dealer_price
        FROM   Inventory    i
        JOIN   Vehicle      v ON i.vehicle_id    = v.vehicle_id
        JOIN   Dealership   d ON i.dealership_id = d.dealership_id
        WHERE  v.fuel_type = 'Electric'
          AND  i.availability_status = 'available'
        ORDER  BY i.price
    """
    show_sql(sql)
    print_table(run_query(sql))
    pause()

def step4_hard_query():
    header(4, "Hard query — H2", "Which dealerships stock 2+ distinct EV models? (GROUP BY + HAVING)")
    say("This query uses GROUP BY and HAVING to find dealerships serious about EVs — not just ones with a single model.")

    sql = """
        SELECT d.dealership_name, d.location,
               COUNT(DISTINCT v.vehicle_id) AS ev_models_in_stock
        FROM   Inventory    i
        JOIN   Vehicle      v ON i.vehicle_id    = v.vehicle_id
        JOIN   Dealership   d ON i.dealership_id = d.dealership_id
        WHERE  v.fuel_type = 'Electric'
          AND  i.availability_status = 'available'
        GROUP  BY d.dealership_id, d.dealership_name, d.location
        HAVING COUNT(DISTINCT v.vehicle_id) >= 2
        ORDER  BY ev_models_in_stock DESC
    """
    show_sql(sql)
    print_table(run_query(sql))
    pause()

def step5_hard_query2():
    header(5, "Hard query — H3", "Customers whose budget exceeds average price for their preferred fuel type")
    say("A correlated aggregation — for each customer we compute the average price of vehicles matching their fuel preference, then filter to customers who can actually afford above average.")

    sql = """
        SELECT c.name, c.budget, c.preferred_fuel_type,
               ROUND(AVG(v.price)::numeric, 2) AS avg_price_for_type
        FROM   Customer c
        JOIN   Vehicle  v ON v.fuel_type = c.preferred_fuel_type
        GROUP  BY c.customer_id, c.name, c.budget, c.preferred_fuel_type
        HAVING c.budget > AVG(v.price)
        ORDER  BY c.budget DESC
    """
    show_sql(sql)
    print_table(run_query(sql))
    pause()

def step6_financing():
    header(6, "Medium query — M3", "Financing options for a specific vehicle (5-table JOIN)")
    say("A customer interested in the Tesla Model Y wants to see financing. This joins 5 tables: Vehicle → Inventory → Dealership → Financing, filtered through SearchHistory.")

    sql = """
        SELECT d.dealership_name, d.location,
               f.interest_rate, f.loan_term_months, f.min_down_payment
        FROM   Vehicle      v
        JOIN   Inventory    i ON v.vehicle_id    = i.vehicle_id
        JOIN   Dealership   d ON i.dealership_id = d.dealership_id
        JOIN   Financing    f ON d.dealership_id = f.dealership_id
        WHERE  v.brand ILIKE '%Tesla%'
          AND  v.model ILIKE '%Model Y%'
          AND  i.availability_status = 'available'
        ORDER  BY f.interest_rate
    """
    show_sql(sql)
    print_table(run_query(sql))
    pause()

def step7_admin_insert():
    header(7, "Admin operation — INSERT", "Dealership adds a new vehicle to inventory")
    say("A dealership administrator adds a Ford F-150 to AutoPlex Cleveland's inventory.")

    sql = """
        INSERT INTO Inventory (vehicle_id, dealership_id, stock_quantity, price, availability_status)
        VALUES (5, 1, 3, 34500.00, 'available')
        ON CONFLICT (vehicle_id, dealership_id)
        DO UPDATE SET stock_quantity = EXCLUDED.stock_quantity,
                      price          = EXCLUDED.price,
                      availability_status = 'available'
    """
    show_sql(sql)
    run_write(sql)
    print("  Insert successful. Verifying...\n")

    verify = run_query("""
        SELECT v.brand, v.model, d.dealership_name,
               i.stock_quantity, i.price, i.availability_status
        FROM   Inventory i
        JOIN   Vehicle    v ON i.vehicle_id    = v.vehicle_id
        JOIN   Dealership d ON i.dealership_id = d.dealership_id
        WHERE  v.vehicle_id = 5 AND i.dealership_id = 1
    """)
    print_table(verify)
    pause()

def step8_admin_update():
    header(8, "Admin operation — UPDATE", "Dealership updates price during a promotion")
    say("AutoPlex Cleveland is running a promotion — they drop the F-150 price by $1,500.")

    sql = """
        UPDATE Inventory
        SET    price = 33000.00
        WHERE  vehicle_id = 5 AND dealership_id = 1
    """
    show_sql(sql)
    run_write(sql)
    print("  Update successful. Verifying new price...\n")

    verify = run_query("""
        SELECT v.brand, v.model, d.dealership_name, i.price
        FROM   Inventory i
        JOIN   Vehicle    v ON i.vehicle_id    = v.vehicle_id
        JOIN   Dealership d ON i.dealership_id = d.dealership_id
        WHERE  v.vehicle_id = 5 AND i.dealership_id = 1
    """)
    print_table(verify)
    pause()

def step9_window():
    header(9, "Hard query — H1", "Cheapest and most expensive vehicle per brand (window function)")
    say("This uses a window function with PARTITION BY — for every vehicle, it shows the min and max price within its brand without collapsing rows.")

    sql = """
        SELECT brand, model, year, price,
               MIN(price) OVER (PARTITION BY brand) AS brand_min,
               MAX(price) OVER (PARTITION BY brand) AS brand_max
        FROM   Vehicle
        ORDER  BY brand, price
        LIMIT  12
    """
    show_sql(sql)
    print_table(run_query(sql))
    pause()

def step10_summary():
    header(10, "Summary", "What this system demonstrates")
    say("AutoSelect implements a fully normalised 6-table PostgreSQL database with:")
    features = [
        "All tables in BCNF — functional dependencies verified",
        "Composite primary key on Inventory (the corrected M:N relationship)",
        "Easy / medium / hard SQL queries including JOINs, GROUP BY, HAVING, subqueries, window functions",
        "Query M2 also expressed in Relational Algebra and Tuple Relational Calculus",
        "Real vehicle data loaded from the 2023 Kaggle Cars Dataset (~300 records)",
        "Synthetic dealership, financing, customer, and search history data via Faker",
        "Python CLI connecting to PostgreSQL via psycopg2 with embedded SQL",
    ]
    for f in features:
        print(f"  + {f}")
    print()
    say("Thank you.")

# ── Entry point ────────────────────────────────────────────────

STEPS = [
    step1_connection,
    step2_easy_query,
    step3_medium_query,
    step4_hard_query,
    step5_hard_query2,
    step6_financing,
    step7_admin_insert,
    step8_admin_update,
    step9_window,
    step10_summary,
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoSelect demo script")
    parser.add_argument("--fast", action="store_true", help="No pauses between steps")
    parser.add_argument("--step", type=int, default=1,  help="Start from step N")
    args = parser.parse_args()

    FAST = args.fast

    print("\n╔══════════════════════════════════════════════════╗")
    print("║   AutoSelect — Live Demo                         ║")
    print("║   CSDS 341: Introduction to Database Systems     ║")
    print("╚══════════════════════════════════════════════════╝")

    try:
        for fn in STEPS[args.step - 1:]:
            fn()
    except psycopg2.Error as e:
        print(f"\n  Database error: {e}")
        print("  Is PostgreSQL running? Check DB_CONFIG at the top of demo.py.\n")
    except KeyboardInterrupt:
        print("\n\n  Demo interrupted.\n")
