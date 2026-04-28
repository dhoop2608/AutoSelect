"""
AutoSelect — Kaggle Data Loader
Loads the 2023 Cars Dataset CSV into the Vehicle table.

Dataset: https://www.kaggle.com/datasets/anoopjohny/2023-cars-dataset
Download the CSV, place it in the same folder as this script, then run:

    pip install psycopg2-binary pandas
    python load_kaggle_data.py

Or pass a custom path:
    python load_kaggle_data.py --file /path/to/cars.csv --preview
"""

import argparse
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ── Config ─────────────────────────────────────────────────────
DB_CONFIG = {
    "dbname":   "autoselect",
    "user":     "dhoopshikhabasgeet",   # change if needed
    "password": "",           # change if needed
    "host":     "localhost",
    "port":     5432,
}

# ── Value mappings ─────────────────────────────────────────────
# Maps whatever values the Kaggle CSV uses to our CHECK constraint values.
# Extend these dicts if you see unmapped values in the preview output.

FUEL_MAP = {
    "gasoline":       "Gas",
    "gas":            "Gas",
    "petrol":         "Gas",
    "regular":        "Gas",
    "premium":        "Gas",
    "diesel":         "Diesel",
    "hybrid":         "Hybrid",
    "plug-in hybrid": "Hybrid",
    "phev":           "Hybrid",
    "electric":       "Electric",
    "ev":             "Electric",
    "battery electric": "Electric",
    "natural gas":    "Gas",    # fallback
}

BODY_MAP = {
    "sedan":        "Sedan",
    "saloon":       "Sedan",
    "suv":          "SUV",
    "crossover":    "SUV",
    "truck":        "Truck",
    "pickup":       "Truck",
    "pickup truck": "Truck",
    "coupe":        "Coupe",
    "hatchback":    "Hatchback",
    "van":          "Van",
    "minivan":      "Van",
    "wagon":        "Hatchback",  # closest match
    "convertible":  "Coupe",      # closest match
}

VALID_FUEL  = {"Gas", "Hybrid", "Electric", "Diesel"}
VALID_BODY  = {"Sedan", "SUV", "Truck", "Coupe", "Hatchback", "Van"}

# ── Column name candidates ─────────────────────────────────────
# The Kaggle CSV may use slightly different column headers depending
# on the version. We try each candidate in order and take the first match.

COL_CANDIDATES = {
    "brand":      ["Make", "make", "Brand", "brand", "Manufacturer", " Car Make "],
    "model":      ["Model", "model", " Car Model   "],
    "year":       ["Year", "year", "Model Year", "model_year", " Year "],
    "price":      ["MSRP", "msrp", "Price", "price", "Base MSRP", " Price ($) "],
    "fuel_type":  ["Fuel", "fuel", "Fuel Type", "fuel_type", "FuelType",
                   "Engine Fuel Type", "EngineFuelType", " Fuel Type "],
    "engine_type":["Engine", "engine", "Engine Type", "engine_type",
                   "Engine Information", "EngineType", "Displacement",
                   " Engine Size (L) "],
    "body_style": ["Body", "body", "Body Style", "body_style", "BodyType",
                   "Body Type", "Type", "type", "Vehicle Style", " Body Type "],
}

def resolve_column(df, candidates):
    """Return the first candidate column name that exists in df, or None."""
    for c in candidates:
        if c in df.columns:
            return c
    return None

# ── Cleaning helpers ───────────────────────────────────────────

def clean_fuel(val):
    if pd.isna(val):
        return None
    mapped = FUEL_MAP.get(str(val).strip().lower())
    return mapped  # None if unrecognised — row will be skipped

def clean_body(val):
    if pd.isna(val):
        return None
    mapped = BODY_MAP.get(str(val).strip().lower())
    return mapped  # None if unrecognised — row will be skipped

def clean_price(val):
    if pd.isna(val):
        return None
    # Strip currency symbols, commas, spaces
    cleaned = str(val).replace("$", "").replace(",", "").strip()
    try:
        price = float(cleaned)
        return price if price > 0 else None
    except ValueError:
        return None

def clean_year(val):
    if pd.isna(val):
        return None
    try:
        year = int(float(str(val).strip()))
        return year if 1980 <= year <= 2030 else None
    except ValueError:
        return None

def clean_str(val, max_len=100):
    if pd.isna(val):
        return None
    return str(val).strip()[:max_len] or None

# ── Main loader ────────────────────────────────────────────────

def load(csv_path: str, preview: bool = False, limit: int = None):
    print(f"\nReading: {csv_path}")
    try:
        df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)

    print(f"Raw CSV: {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns found: {list(df.columns)}\n")

    # Resolve column names
    col = {field: resolve_column(df, candidates)
           for field, candidates in COL_CANDIDATES.items()}

    missing_required = [f for f in ("brand", "model", "year", "price")
                        if col[f] is None]
    if missing_required:
        print(f"ERROR: Could not find required columns: {missing_required}")
        print("Check COL_CANDIDATES at the top of this script and add the")
        print("actual column names from your CSV.")
        sys.exit(1)

    print("Column mapping resolved:")
    for field, found in col.items():
        status = found if found else "(not found — will be NULL)"
        print(f"  {field:12} ← {status}")
    print()

    if preview:
        print("Preview (first 5 rows after mapping):")
        print(df[[v for v in col.values() if v]].head())
        print("\nRun without --preview to load into the database.\n")
        return

    # Build cleaned rows
    rows = []
    skipped = 0
    skip_reasons = {}

    sample = df.head(limit) if limit else df

    for _, raw in sample.iterrows():
        brand  = clean_str(raw[col["brand"]], 50)  if col["brand"]       else None
        model  = clean_str(raw[col["model"]], 50)  if col["model"]       else None
        year   = clean_year(raw[col["year"]])       if col["year"]        else None
        price  = clean_price(raw[col["price"]])     if col["price"]       else None
        fuel   = clean_fuel(raw[col["fuel_type"]])  if col["fuel_type"]   else None
        engine = clean_str(raw[col["engine_type"]],50) if col["engine_type"] else None
        body   = clean_body(raw[col["body_style"]]) if col["body_style"]  else None

        # Required fields
        if not brand:
            skip_reasons["missing brand"] = skip_reasons.get("missing brand", 0) + 1
            skipped += 1; continue
        if not model:
            skip_reasons["missing model"] = skip_reasons.get("missing model", 0) + 1
            skipped += 1; continue
        if year is None:
            skip_reasons["invalid year"] = skip_reasons.get("invalid year", 0) + 1
            skipped += 1; continue
        if price is None:
            skip_reasons["invalid price"] = skip_reasons.get("invalid price", 0) + 1
            skipped += 1; continue
        if fuel is None:
            skip_reasons["unmapped fuel"] = skip_reasons.get("unmapped fuel", 0) + 1
            skipped += 1; continue

        rows.append((brand, model, year, price, fuel, engine, body))

    print(f"Rows ready to insert: {len(rows)}")
    print(f"Rows skipped:         {skipped}")
    if skip_reasons:
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            print(f"  {count:4}  {reason}")
    print()

    if not rows:
        print("Nothing to insert. Check the column mapping and FUEL_MAP above.")
        return

    # Insert into PostgreSQL
    sql = """
        INSERT INTO Vehicle (brand, model, year, price, fuel_type, engine_type, body_style)
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    print("Connecting to database...")
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, rows, page_size=100)
            conn.commit()
        print(f"Done. {len(rows)} vehicles inserted into Vehicle table.\n")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


# ── Unmapped value reporter ────────────────────────────────────

def report_unmapped(csv_path: str):
    """Print all unique fuel/body values in the CSV so you can update the maps."""
    try:
        df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)

    fuel_col = resolve_column(df, COL_CANDIDATES["fuel_type"])
    body_col = resolve_column(df, COL_CANDIDATES["body_style"])

    if fuel_col:
        vals = df[fuel_col].dropna().str.strip().str.lower().unique()
        unmapped = [v for v in vals if v not in FUEL_MAP]
        print(f"\nUnmapped fuel values ({len(unmapped)}):")
        for v in sorted(unmapped):
            print(f"  '{v}'")

    if body_col:
        vals = df[body_col].dropna().str.strip().str.lower().unique()
        unmapped = [v for v in vals if v not in BODY_MAP]
        print(f"\nUnmapped body style values ({len(unmapped)}):")
        for v in sorted(unmapped):
            print(f"  '{v}'")
    print()


# ── Entry point ────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Kaggle vehicle CSV into AutoSelect")
    parser.add_argument("--file",    default="cars_2023.csv", help="Path to CSV file")
    parser.add_argument("--preview", action="store_true",     help="Show column mapping without inserting")
    parser.add_argument("--unmapped",action="store_true",     help="Show unrecognised fuel/body values")
    parser.add_argument("--limit",   type=int, default=None,  help="Only load first N rows (for testing)")
    args = parser.parse_args()

    if args.unmapped:
        report_unmapped(args.file)
    else:
        load(args.file, preview=args.preview, limit=args.limit)
