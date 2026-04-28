-- AutoSelect: Intelligent Car Recommendation & Inventory Management System
-- Database Setup: Schema + Sample Data
-- DBMS: PostgreSQL 14+

-- ============================================================
-- DROP TABLES (safe re-run order, children before parents)
-- ============================================================
DROP TABLE IF EXISTS SearchHistory;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS Financing;
DROP TABLE IF EXISTS Vehicle;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Dealership;

-- ============================================================
-- TABLE: Customer
-- FDs: customer_id -> all attributes
-- BCNF: yes (customer_id is the only determinant)
-- ============================================================
CREATE TABLE Customer (
    customer_id          SERIAL          PRIMARY KEY,
    name                 VARCHAR(100)    NOT NULL,
    email                VARCHAR(100)    UNIQUE NOT NULL,
    budget               DECIMAL(10,2),
    preferred_fuel_type  VARCHAR(20)     CHECK (preferred_fuel_type IN ('Gas','Hybrid','Electric','Diesel')),
    preferred_body_style VARCHAR(30)     CHECK (preferred_body_style IN ('Sedan','SUV','Truck','Coupe','Hatchback','Van'))
);

-- ============================================================
-- TABLE: Vehicle
-- FDs: vehicle_id -> all attributes
-- BCNF: yes
-- ============================================================
CREATE TABLE Vehicle (
    vehicle_id   SERIAL          PRIMARY KEY,
    brand        VARCHAR(50)     NOT NULL,
    model        VARCHAR(50)     NOT NULL,
    year         INT             NOT NULL CHECK (year BETWEEN 1980 AND 2030),
    price        DECIMAL(10,2)   NOT NULL CHECK (price > 0),
    fuel_type    VARCHAR(20)     NOT NULL CHECK (fuel_type IN ('Gas','Hybrid','Electric','Diesel')),
    engine_type  VARCHAR(50),
    body_style   VARCHAR(30)     CHECK (body_style IN ('Sedan','SUV','Truck','Coupe','Hatchback','Van'))
);

-- ============================================================
-- TABLE: Dealership
-- FDs: dealership_id -> all attributes
-- BCNF: yes
-- ============================================================
CREATE TABLE Dealership (
    dealership_id   SERIAL          PRIMARY KEY,
    dealership_name VARCHAR(100)    NOT NULL,
    location        VARCHAR(150),
    contact_email   VARCHAR(100),
    phone_number    VARCHAR(20)
);

-- ============================================================
-- TABLE: Inventory
-- Merges the stocked_in (Vehicle-Dealership) M:N relationship.
-- Per ER-to-relational rules for M:N, BOTH FK attributes form
-- the composite PK. A vehicle appears at most once per dealership.
-- FDs: (vehicle_id, dealership_id) -> stock_quantity, price, availability_status
-- BCNF: yes (composite PK is the only determinant)
-- ============================================================
CREATE TABLE Inventory (
    vehicle_id          INT             NOT NULL,
    dealership_id       INT             NOT NULL,
    stock_quantity      INT             NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    price               DECIMAL(10,2)   CHECK (price > 0),
    availability_status VARCHAR(20)     NOT NULL DEFAULT 'available'
                            CHECK (availability_status IN ('available','out_of_stock','discontinued')),
    PRIMARY KEY (vehicle_id, dealership_id),
    FOREIGN KEY (vehicle_id)    REFERENCES Vehicle(vehicle_id)    ON DELETE CASCADE,
    FOREIGN KEY (dealership_id) REFERENCES Dealership(dealership_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: Financing
-- A dealership can offer many financing plans (1:N).
-- FDs: financing_id -> all attributes
-- BCNF: yes (financing_id is sole determinant; dealership_id
--       does NOT determine rate/term since one dealer has many plans)
-- ============================================================
CREATE TABLE Financing (
    financing_id        SERIAL          PRIMARY KEY,
    dealership_id       INT             NOT NULL,
    interest_rate       DECIMAL(5,2)    NOT NULL CHECK (interest_rate >= 0),
    loan_term_months    INT             NOT NULL CHECK (loan_term_months > 0),
    min_down_payment    DECIMAL(10,2)   CHECK (min_down_payment >= 0),
    FOREIGN KEY (dealership_id) REFERENCES Dealership(dealership_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: SearchHistory
-- Logs each customer search. search_id is a surrogate PK because
-- a customer may legitimately search the same vehicle many times.
-- filter_fuel_type / filter_body_style are search INPUT parameters,
-- not derived from vehicle_id — this avoids a BCNF violation.
-- FDs: search_id -> all attributes
-- BCNF: yes
-- ============================================================
CREATE TABLE SearchHistory (
    search_id           SERIAL          PRIMARY KEY,
    customer_id         INT             NOT NULL,
    vehicle_id          INT,
    search_budget       DECIMAL(10,2),
    filter_fuel_type    VARCHAR(20)     CHECK (filter_fuel_type IN ('Gas','Hybrid','Electric','Diesel')),
    filter_body_style   VARCHAR(30)     CHECK (filter_body_style IN ('Sedan','SUV','Truck','Coupe','Hatchback','Van')),
    search_date         DATE            NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id)  REFERENCES Vehicle(vehicle_id)   ON DELETE SET NULL
);

-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Dealerships (10 synthetic records)
INSERT INTO Dealership (dealership_name, location, contact_email, phone_number) VALUES
('AutoPlex Cleveland',      'Cleveland, OH',      'info@autoplex-cle.com',    '216-555-0101'),
('Lakefront Motors',        'Lakewood, OH',       'sales@lakefrontmotors.com','216-555-0202'),
('BayView Auto',            'Bay Village, OH',    'contact@bayviewauto.com',  '440-555-0303'),
('Prestige Motors',         'Beachwood, OH',      'sales@prestigemotors.com', '216-555-0404'),
('Metro Auto Group',        'Parma, OH',          'info@metroautogroup.com',  '440-555-0505'),
('EV Specialists Ohio',     'Westlake, OH',       'ev@evspecialistsoh.com',   '440-555-0606'),
('Buckeye Auto Center',     'Strongsville, OH',   'team@buckeyeauto.com',     '440-555-0707'),
('Summit Car Group',        'Akron, OH',          'info@summitcargroup.com',  '330-555-0808'),
('North Coast Autos',       'Mentor, OH',         'sales@northcoastautos.com','440-555-0909'),
('Crossroads Auto',         'Medina, OH',         'hello@crossroadsauto.com', '330-555-1001');

-- Vehicles (20 records from Kaggle-style vehicle data)
INSERT INTO Vehicle (brand, model, year, price, fuel_type, engine_type, body_style) VALUES
('Toyota',  'Camry',         2023, 28000.00, 'Gas',      '2.5L I4',          'Sedan'),
('Toyota',  'RAV4 Hybrid',   2023, 34000.00, 'Hybrid',   '2.5L I4 Hybrid',   'SUV'),
('Tesla',   'Model 3',       2023, 42990.00, 'Electric', 'Dual Motor',        'Sedan'),
('Tesla',   'Model Y',       2023, 48990.00, 'Electric', 'Long Range Motor',  'SUV'),
('Ford',    'F-150',         2023, 35000.00, 'Gas',      '3.5L V6 EcoBoost', 'Truck'),
('Ford',    'Mustang Mach-E', 2023, 45995.00, 'Electric', 'Rear Motor',       'SUV'),
('Honda',   'Accord',        2023, 27895.00, 'Gas',      '1.5L Turbo I4',    'Sedan'),
('Honda',   'CR-V Hybrid',   2023, 32750.00, 'Hybrid',   '2.0L I4 Hybrid',   'SUV'),
('Chevrolet','Silverado',    2023, 37200.00, 'Gas',      '5.3L V8',          'Truck'),
('Chevrolet','Bolt EV',      2023, 26500.00, 'Electric', 'Front Motor',       'Hatchback'),
('BMW',     '3 Series',      2023, 43300.00, 'Gas',      '2.0L Turbo I4',    'Sedan'),
('BMW',     'iX',            2023, 87100.00, 'Electric', 'Dual Motor',        'SUV'),
('Hyundai', 'Tucson Hybrid', 2023, 30450.00, 'Hybrid',   '1.6L Turbo Hybrid','SUV'),
('Hyundai', 'IONIQ 6',       2023, 38615.00, 'Electric', 'Rear Motor',        'Sedan'),
('Kia',     'Telluride',     2023, 35690.00, 'Gas',      '3.8L V6',          'SUV'),
('Kia',     'EV6',           2023, 42600.00, 'Electric', 'Rear Motor',        'SUV'),
('Volkswagen','Jetta',       2023, 22995.00, 'Gas',      '1.5L Turbo I4',    'Sedan'),
('Volkswagen','ID.4',        2023, 38995.00, 'Electric', 'Rear Motor',        'SUV'),
('Subaru',  'Outback',       2023, 28895.00, 'Gas',      '2.5L H4',          'SUV'),
('Subaru',  'Forester',      2023, 27895.00, 'Gas',      '2.5L H4',          'SUV');

-- Inventory (vehicle_id, dealership_id, stock_quantity, price, availability_status)
INSERT INTO Inventory (vehicle_id, dealership_id, stock_quantity, price, availability_status) VALUES
(1,  1, 5,  27500.00, 'available'),
(2,  1, 3,  33500.00, 'available'),
(3,  6, 4,  42990.00, 'available'),
(4,  6, 2,  48990.00, 'available'),
(5,  2, 7,  34800.00, 'available'),
(6,  6, 1,  45995.00, 'available'),
(7,  3, 6,  27500.00, 'available'),
(8,  3, 4,  32200.00, 'available'),
(9,  5, 8,  36900.00, 'available'),
(10, 6, 3,  26000.00, 'available'),
(11, 4, 2,  43300.00, 'available'),
(12, 4, 1,  87100.00, 'available'),
(13, 7, 5,  30000.00, 'available'),
(14, 6, 3,  38615.00, 'available'),
(15, 8, 4,  35200.00, 'available'),
(16, 6, 2,  42600.00, 'available'),
(17, 9, 9,  22500.00, 'available'),
(18, 6, 3,  38500.00, 'available'),
(19,10, 4,  28500.00, 'available'),
(20,10, 3,  27500.00, 'available'),
(1,  2, 2,  27800.00, 'available'),
(3,  4, 1,  43200.00, 'available'),
(5,  8, 3,  35100.00, 'available'),
(10, 7, 2,  26200.00, 'available');

-- Financing (synthetic plans per dealership)
INSERT INTO Financing (dealership_id, interest_rate, loan_term_months, min_down_payment) VALUES
(1, 4.99, 60, 2000.00),
(1, 6.49, 72, 1000.00),
(2, 3.99, 48, 2500.00),
(3, 5.25, 60, 1500.00),
(4, 5.99, 72, 3000.00),
(5, 4.50, 60, 1000.00),
(6, 2.99, 60, 2000.00),
(6, 0.00, 36, 5000.00),
(7, 4.75, 60, 1500.00),
(8, 5.50, 72, 1000.00),
(9, 4.25, 48, 2000.00),
(10,5.75, 60, 1500.00);

-- Customers (10 synthetic records)
INSERT INTO Customer (name, email, budget, preferred_fuel_type, preferred_body_style) VALUES
('Sarah Johnson',    'sarah.j@email.com',    35000.00, 'Electric', 'SUV'),
('Marcus Williams',  'mwilliams@email.com',  28000.00, 'Gas',      'Sedan'),
('Priya Patel',      'priya.p@email.com',    50000.00, 'Electric', 'Sedan'),
('James Carter',     'jcarter@email.com',    40000.00, 'Hybrid',   'SUV'),
('Olivia Reed',      'o.reed@email.com',     25000.00, 'Gas',      'Sedan'),
('David Kim',        'dkim@email.com',       45000.00, 'Electric', 'SUV'),
('Emma Torres',      'e.torres@email.com',   30000.00, 'Hybrid',   'SUV'),
('Nathan Brooks',    'nbrooks@email.com',    60000.00, 'Electric', 'Sedan'),
('Aaliyah Moore',    'a.moore@email.com',    33000.00, 'Gas',      'Truck'),
('Tyler Evans',      't.evans@email.com',    27000.00, 'Gas',      'SUV');

-- SearchHistory
INSERT INTO SearchHistory (customer_id, vehicle_id, search_budget, filter_fuel_type, filter_body_style, search_date) VALUES
(1, 4,  50000.00, 'Electric', 'SUV',    '2026-03-01'),
(1, 6,  50000.00, 'Electric', 'SUV',    '2026-03-02'),
(2, 1,  30000.00, 'Gas',      'Sedan',  '2026-03-05'),
(3, 3,  45000.00, 'Electric', 'Sedan',  '2026-03-06'),
(4, 8,  35000.00, 'Hybrid',   'SUV',    '2026-03-07'),
(5, 7,  28000.00, 'Gas',      'Sedan',  '2026-03-08'),
(6, 12, 90000.00, 'Electric', 'SUV',    '2026-03-10'),
(7, 13, 32000.00, 'Hybrid',   'SUV',    '2026-03-11'),
(8, 14, 40000.00, 'Electric', 'Sedan',  '2026-03-12'),
(9, 5,  38000.00, 'Gas',      'Truck',  '2026-03-13'),
(2, 17, 25000.00, 'Gas',      'Sedan',  '2026-03-14'),
(1, 18, 40000.00, 'Electric', 'SUV',    '2026-03-15');
