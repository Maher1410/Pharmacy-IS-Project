create database Pharm;
use Pharm;
-- 1. MedicineCategories
CREATE TABLE MedicineCategories (
    CategoryID INTEGER PRIMARY KEY AUTO_INCREMENT,
    CategoryName VARCHAR(100)
);

INSERT INTO MedicineCategories (CategoryName) VALUES
('Painkiller'),
('Antibiotic'),
('Cough & Cold');

-- 2. Medicines
CREATE TABLE Medicines (
    MedicineID INTEGER PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Manufacturer VARCHAR(100),
    ExpiryDate DATE,
    Price DECIMAL(10, 2),
    Stock INT,
    CategoryID INT,
    FOREIGN KEY (CategoryID) REFERENCES MedicineCategories(CategoryID)
);

INSERT INTO Medicines (Name, Manufacturer, ExpiryDate, Price, Stock, CategoryID) VALUES
('Paracetamol', 'ABC Pharma', '2026-03-01', 5.00, 100, 1),
('Amoxicillin', 'XYZ Labs', '2025-12-15', 12.50, 50, 2),
('Cough Syrup', 'MedCare', '2026-01-10', 7.80, 30, 3);

-- 3. Suppliers
CREATE TABLE Suppliers (
    SupplierID INTEGER PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    ContactNumber VARCHAR(20),
    Email VARCHAR(100),
    Address VARCHAR(255)
);

INSERT INTO Suppliers (Name, ContactNumber, Email, Address) VALUES
('Global Pharma Supply', '1234567890', 'contact@globalpharma.com', '123 Main St, City A'),
('HealthFirst Distributors', '9876543210', 'support@healthfirst.com', '456 Elm St, City B');

-- 4. Purchases
CREATE TABLE Purchases (
    PurchaseID INTEGER PRIMARY KEY AUTO_INCREMENT,
    SupplierID INT,
    MedicineID INT,
    Quantity INT,
    PurchaseDate DATE,
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID),
    FOREIGN KEY (MedicineID) REFERENCES Medicines(MedicineID)
);

INSERT INTO Purchases (SupplierID, MedicineID, Quantity, PurchaseDate) VALUES
(1, 1, 200, '2025-01-15'),
(2, 2, 100, '2025-01-18'),
(1, 3, 50, '2025-02-10');

-- 5. Customers
CREATE TABLE Customers (
    CustomerID INTEGER PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    ContactNumber VARCHAR(20),
    Email VARCHAR(100)
);

INSERT INTO Customers (Name, ContactNumber, Email) VALUES
('John Doe', '1112223333', 'john.doe@example.com'),
('Jane Smith', '4445556666', 'jane.smith@example.com');

-- 6. Sales
CREATE TABLE Sales (
    SaleID INTEGER PRIMARY KEY AUTO_INCREMENT,
    CustomerID INT,
    MedicineID INT,
    Quantity INT,
    SaleDate DATE,
    TotalAmount DECIMAL(10, 2),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (MedicineID) REFERENCES Medicines(MedicineID)
);

INSERT INTO Sales (CustomerID, MedicineID, Quantity, SaleDate, TotalAmount) VALUES
(1, 1, 2, '2025-03-10', 10.00),
(2, 2, 1, '2025-03-11', 12.50),
(1, 3, 1, '2025-03-12', 7.80);

-- 7. Employees
CREATE TABLE Employees (
    EmployeeID INTEGER PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    Role VARCHAR(50),
    Salary DECIMAL(10, 2),
    HireDate DATE,
    ContactNumber VARCHAR(20)
);

INSERT INTO Employees (Name, Role, Salary, HireDate, ContactNumber) VALUES
('Alice Johnson', 'Pharmacist', 3000.00, '2024-08-01', '5550001111'),
('Bob Lee', 'Cashier', 1800.00, '2024-09-15', '5552223333');

-- 8. Doctors
CREATE TABLE Doctors (
    DoctorID INTEGER PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    Specialization VARCHAR(100),
    ContactNumber VARCHAR(20),
    Email VARCHAR(100)
);

INSERT INTO Doctors (Name, Specialization, ContactNumber, Email) VALUES
('Dr. Adams', 'General Physician', '1231231234', 'dr.adams@example.com'),
('Dr. Taylor', 'Pediatrics', '2342342345', 'dr.taylor@example.com');

-- 9. Prescriptions
CREATE TABLE Prescriptions (
    PrescriptionID INTEGER PRIMARY KEY AUTO_INCREMENT,
    DoctorID INT,
    CustomerID INT,
    DateIssued DATE,
    Notes TEXT,
    FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);

INSERT INTO Prescriptions (DoctorID, CustomerID, DateIssued, Notes) VALUES
(1, 1, '2025-03-09', 'Fever and body pain'),
(2, 2, '2025-03-10', 'Child cough');

-- 10. PrescriptionDetails
CREATE TABLE PrescriptionDetails (
    PrescriptionDetailID INTEGER PRIMARY KEY AUTO_INCREMENT,
    PrescriptionID INT,
    MedicineID INT,
    Dosage VARCHAR(100),
    Duration VARCHAR(50),
    FOREIGN KEY (PrescriptionID) REFERENCES Prescriptions(PrescriptionID),
    FOREIGN KEY (MedicineID) REFERENCES Medicines(MedicineID)
);

INSERT INTO PrescriptionDetails (PrescriptionID, MedicineID, Dosage, Duration) VALUES
(1, 1, '500mg twice a day', '5 days'),
(2, 3, '10ml thrice a day', '7 days');

-- 11. InventoryLogs
CREATE TABLE InventoryLogs (
    LogID INTEGER PRIMARY KEY AUTO_INCREMENT,
    MedicineID INT,
    ChangeType ENUM('Added', 'Removed', 'Sold', 'Expired'),
    QuantityChanged INT,
    ChangeDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Notes TEXT,
    FOREIGN KEY (MedicineID) REFERENCES Medicines(MedicineID)
);

INSERT INTO InventoryLogs (MedicineID, ChangeType, QuantityChanged, Notes) VALUES
(1, 'Added', 200, 'Initial stock received'),
(1, 'Sold', -2, 'Sale to John Doe'),
(2, 'Sold', -1, 'Sale to Jane Smith'),
(3, 'Added', 50, 'New stock from supplier'),
(3, 'Sold', -1, 'Sold via prescription');