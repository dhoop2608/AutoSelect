-- AutoSelect: Query File
-- Covers: Easy, Medium, Hard SQL + Relational Algebra + TRC
-- DBMS: PostgreSQL 14+

-- ============================================================
-- EASY QUERIES  (single table, simple WHERE / ORDER BY)
-- ============================================================

-- E1: All electric vehicles under $45,000, sorted by price
SELECT vehicle_id, brand, model, year, price
FROM Vehicle
WHERE fuel_type = 'Electric'
  AND price < 45000
ORDER BY price ASC;

-- E2: All vehicles made by Toyota or Honda
SELECT vehicle_id, brand, model, year, price, fuel_type
FROM Vehicle
WHERE brand IN ('Toyota', 'Honda')
ORDER BY brand, price;

-- E3: All customers whose budget is at least $40,000
SELECT customer_id, name, email, budget, preferred_fuel_type
FROM Customer
WHERE budget >= 40000
ORDER BY budget DESC;

-- E4: All dealerships located in Ohio (location contains 'OH')
SELECT dealership_id, dealership_name, location, phone_number
FROM Dealership
WHERE location LIKE '%, OH';

-- E5: All financing plans with interest rate below 4%
SELECT f.financing_id, d.dealership_name, f.interest_rate,
       f.loan_term_months, f.min_down_payment
FROM Financing f
JOIN Dealership d ON f.dealership_id = d.dealership_id
WHERE f.interest_rate < 4.00
ORDER BY f.interest_rate;


-- ============================================================
-- MEDIUM QUERIES  (multi-table JOINs, aggregation)
-- ============================================================

-- M1: All vehicles currently in stock at a given dealership
--     (example: dealership_id = 6, EV Specialists Ohio)
SELECT v.brand, v.model, v.year, v.fuel_type,
       i.stock_quantity, i.price, i.availability_status
FROM Inventory i
JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
WHERE i.dealership_id = 6
  AND i.availability_status = 'available'
ORDER BY i.price;

-- M2: All electric vehicles available at any dealership,
--     showing dealership name and inventory price
SELECT v.brand, v.model, v.year,
       d.dealership_name, d.location,
       i.stock_quantity, i.price AS dealer_price
FROM Inventory i
JOIN Vehicle    v ON i.vehicle_id    = v.vehicle_id
JOIN Dealership d ON i.dealership_id = d.dealership_id
WHERE v.fuel_type = 'Electric'
  AND i.availability_status = 'available'
ORDER BY i.price;

-- M3: All financing options available for a vehicle a customer
--     is interested in — given customer_id = 1 (Sarah Johnson)
SELECT v.brand, v.model, d.dealership_name,
       f.interest_rate, f.loan_term_months, f.min_down_payment
FROM SearchHistory sh
JOIN Vehicle    v  ON sh.vehicle_id    = v.vehicle_id
JOIN Inventory  i  ON v.vehicle_id     = i.vehicle_id
JOIN Dealership d  ON i.dealership_id  = d.dealership_id
JOIN Financing  f  ON d.dealership_id  = f.dealership_id
WHERE sh.customer_id = 1
ORDER BY f.interest_rate;

-- M4: Count of available vehicles by fuel type across all dealerships
SELECT v.fuel_type,
       COUNT(DISTINCT v.vehicle_id) AS unique_models,
       SUM(i.stock_quantity)        AS total_stock
FROM Inventory i
JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
WHERE i.availability_status = 'available'
GROUP BY v.fuel_type
ORDER BY total_stock DESC;

-- M5: Each customer's most recent search
SELECT c.name, v.brand, v.model, sh.filter_fuel_type,
       sh.search_budget, sh.search_date
FROM SearchHistory sh
JOIN Customer c ON sh.customer_id = c.customer_id
JOIN Vehicle  v ON sh.vehicle_id  = v.vehicle_id
WHERE sh.search_date = (
    SELECT MAX(sh2.search_date)
    FROM SearchHistory sh2
    WHERE sh2.customer_id = sh.customer_id
)
ORDER BY sh.search_date DESC;


-- ============================================================
-- HARD QUERIES  (subqueries, GROUP BY + HAVING, window functions)
-- ============================================================

-- H1: Cheapest and most expensive vehicle within each brand
--     (uses window functions — good for report discussion)
SELECT brand, model, year, price, fuel_type,
       MIN(price) OVER (PARTITION BY brand) AS brand_min_price,
       MAX(price) OVER (PARTITION BY brand) AS brand_max_price
FROM Vehicle
ORDER BY brand, price;

-- H2: Dealerships that stock MORE than 2 distinct electric vehicle models
SELECT d.dealership_name, d.location,
       COUNT(DISTINCT v.vehicle_id) AS ev_models_in_stock
FROM Inventory  i
JOIN Vehicle    v ON i.vehicle_id    = v.vehicle_id
JOIN Dealership d ON i.dealership_id = d.dealership_id
WHERE v.fuel_type = 'Electric'
  AND i.availability_status = 'available'
GROUP BY d.dealership_id, d.dealership_name, d.location
HAVING COUNT(DISTINCT v.vehicle_id) > 2
ORDER BY ev_models_in_stock DESC;

-- H3: Customers whose budget EXCEEDS the average price of
--     vehicles matching their preferred fuel type
--     (correlated subquery)
SELECT c.name, c.budget, c.preferred_fuel_type,
       ROUND(AVG(v.price)::numeric, 2) AS avg_price_for_type
FROM Customer c
JOIN Vehicle v ON v.fuel_type = c.preferred_fuel_type
GROUP BY c.customer_id, c.name, c.budget, c.preferred_fuel_type
HAVING c.budget > AVG(v.price)
ORDER BY c.budget DESC;

-- H4: For each brand, the vehicle with the lowest dealer price
--     currently available anywhere (uses subquery + JOIN)
SELECT v.brand, v.model, v.year, v.fuel_type,
       d.dealership_name, i.price AS lowest_dealer_price
FROM Inventory  i
JOIN Vehicle    v ON i.vehicle_id    = v.vehicle_id
JOIN Dealership d ON i.dealership_id = d.dealership_id
WHERE i.price = (
    SELECT MIN(i2.price)
    FROM Inventory i2
    JOIN Vehicle v2 ON i2.vehicle_id = v2.vehicle_id
    WHERE v2.brand = v.brand
      AND i2.availability_status = 'available'
)
AND i.availability_status = 'available'
ORDER BY v.brand;


-- ============================================================
-- RELATIONAL ALGEBRA  (written as comments — for report)
-- ============================================================

-- Query M2 expressed in Relational Algebra:
-- "All electric vehicles available at any dealership"
--
-- Step 1 — select electric vehicles:
--   EV ← σ(fuel_type='Electric')(Vehicle)
--
-- Step 2 — select available inventory:
--   AvailInv ← σ(availability_status='available')(Inventory)
--
-- Step 3 — join inventory with electric vehicles:
--   EVInv ← EV ⋈(Vehicle.vehicle_id = Inventory.vehicle_id) AvailInv
--
-- Step 4 — join with dealership:
--   Result ← EVInv ⋈(Inventory.dealership_id = Dealership.dealership_id) Dealership
--
-- Step 5 — project relevant columns:
--   Final ← π(brand, model, year, dealership_name, location, stock_quantity, price)(Result)
--
-- Full expression:
--   π(brand,model,year,dealership_name,location,stock_quantity,price) (
--     σ(fuel_type='Electric')(Vehicle)
--     ⋈ σ(availability_status='available')(Inventory)
--     ⋈ Dealership
--   )


-- ============================================================
-- TUPLE RELATIONAL CALCULUS  (written as comments — for report)
-- ============================================================

-- Query M2 expressed in TRC:
-- "All electric vehicles available at any dealership"
--
-- { t | ∃v ∈ Vehicle ∃i ∈ Inventory ∃d ∈ Dealership (
--       v.vehicle_id    = i.vehicle_id
--     ∧ i.dealership_id = d.dealership_id
--     ∧ v.fuel_type     = 'Electric'
--     ∧ i.availability_status = 'available'
--     ∧ t.brand         = v.brand
--     ∧ t.model         = v.model
--     ∧ t.year          = v.year
--     ∧ t.dealership_name = d.dealership_name
--     ∧ t.location      = d.location
--     ∧ t.stock_quantity = i.stock_quantity
--     ∧ t.price         = i.price
-- ) }
--
-- Plain English: "Find all tuples t such that there exists a vehicle v,
-- an inventory record i, and a dealership d where v is electric,
-- the inventory entry is available, and they all share the same keys."
