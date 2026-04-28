# AutoSelect — Web UI

## Setup

```bash
pip install flask psycopg2-binary
```

Make sure your PostgreSQL database is running with the AutoSelect schema loaded.

Edit `app.py` line 13 if your DB username/password differ:
```python
DB_CONFIG = {
    "dbname":   "autoselect",
    "user":     "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "host":     "localhost",
    "port":     5432,
}
```

## Run

```bash
python app.py
```

Then open: http://localhost:5050

## Features

### Customer View
- **Browse Vehicles** — filter by fuel type, body style, brand, and max budget
- Click any vehicle card to see full details, dealership availability, and financing options
- **Dealerships** — browse all dealerships and click to see their full inventory
- **Insights** — stock breakdown by fuel type, EV leader dealerships

### Admin View
- **Manage Inventory** — filter by dealership, edit stock/price, discontinue listings
- **Add Vehicle** — register a new vehicle model to the catalogue

## File Structure

```
autoselect/
├── app.py              # Flask backend (all API routes)
├── requirements.txt
├── templates/
│   └── index.html      # Single-page frontend
└── README.md
```
