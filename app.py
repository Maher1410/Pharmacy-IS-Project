from flask import Flask, render_template, request, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin1234',
    'database': 'Pharm'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

# Medicine Categories Endpoints
@app.route('/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM MedicineCategories")
        categories = cursor.fetchall()
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM MedicineCategories WHERE CategoryID = %s", (category_id,))
        category = cursor.fetchone()
        return jsonify(category) if category else ('', 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/categories', methods=['POST'])
def add_category():
    try:
        data = request.get_json()
        if 'CategoryName' not in data:
            return jsonify({'error': 'Missing CategoryName'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO MedicineCategories (CategoryName) VALUES (%s)", (data['CategoryName'],))
        conn.commit()
        return jsonify({'message': 'Category added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    try:
        data = request.get_json()
        if 'CategoryName' not in data:
            return jsonify({'error': 'Missing CategoryName'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE MedicineCategories SET CategoryName = %s WHERE CategoryID = %s",
                       (data['CategoryName'], category_id))
        conn.commit()
        return jsonify({'message': 'Category updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM MedicineCategories WHERE CategoryID = %s", (category_id,))
        conn.commit()
        return jsonify({'message': 'Category deleted successfully'})
    except mysql.connector.IntegrityError as e:
        return jsonify({'error': 'Cannot delete category referenced by medicines'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Medicines Endpoints
@app.route('/medicines', methods=['GET'])
def get_medicines():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*, c.CategoryName 
            FROM Medicines m
            JOIN MedicineCategories c ON m.CategoryID = c.CategoryID
        """)
        medicines = cursor.fetchall()
        return jsonify(medicines)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/medicines/<int:medicine_id>', methods=['GET'])
def get_medicine(medicine_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*, c.CategoryName 
            FROM Medicines m
            JOIN MedicineCategories c ON m.CategoryID = c.CategoryID
            WHERE m.MedicineID = %s
        """, (medicine_id,))
        medicine = cursor.fetchone()
        return jsonify(medicine) if medicine else ('', 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/medicines', methods=['POST'])
def add_medicine():
    try:
        data = request.get_json()
        required_fields = ['Name', 'Manufacturer', 'ExpiryDate', 'Price', 'Stock', 'CategoryID']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate CategoryID exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CategoryID FROM MedicineCategories WHERE CategoryID = %s", (data['CategoryID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Invalid CategoryID'}), 400

        # Validate date format
        try:
            datetime.strptime(data['ExpiryDate'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid ExpiryDate format (use YYYY-MM-DD)'}), 400

        cursor.execute("""
            INSERT INTO Medicines (Name, Manufacturer, ExpiryDate, Price, Stock, CategoryID)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['Name'],
            data['Manufacturer'],
            data['ExpiryDate'],
            float(data['Price']),
            int(data['Stock']),
            int(data['CategoryID'])
        ))
        conn.commit()
        return jsonify({'message': 'Medicine added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/medicines/<int:medicine_id>', methods=['PUT'])
def update_medicine(medicine_id):
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validate medicine exists
        cursor.execute("SELECT MedicineID FROM Medicines WHERE MedicineID = %s", (medicine_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Medicine not found'}), 404

        updates = []
        params = []
        fields = {
            'Name': 'Name',
            'Manufacturer': 'Manufacturer',
            'ExpiryDate': 'ExpiryDate',
            'Price': 'Price',
            'Stock': 'Stock',
            'CategoryID': 'CategoryID'
        }

        for key, db_field in fields.items():
            if key in data:
                if key == 'ExpiryDate':
                    try:  # Validate date
                        datetime.strptime(data[key], '%Y-%m-%d')
                    except ValueError:
                        return jsonify({'error': 'Invalid ExpiryDate format'}), 400
                updates.append(f"{db_field} = %s")
                params.append(data[key] if key not in ['Price', 'Stock', 'CategoryID'] 
                            else float(data[key]) if key == 'Price' 
                            else int(data[key]))

        if 'CategoryID' in data:  # Validate new CategoryID
            cursor.execute("SELECT CategoryID FROM MedicineCategories WHERE CategoryID = %s", (data['CategoryID'],))
            if not cursor.fetchone():
                return jsonify({'error': 'Invalid CategoryID'}), 400

        if not updates:
            return jsonify({'error': 'No fields to update'}), 400

        params.append(medicine_id)
        cursor.execute(f"UPDATE Medicines SET {', '.join(updates)} WHERE MedicineID = %s", params)
        conn.commit()
        return jsonify({'message': 'Medicine updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/medicines/<int:medicine_id>', methods=['DELETE'])
def delete_medicine(medicine_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Medicines WHERE MedicineID = %s", (medicine_id,))
        conn.commit()
        return jsonify({'message': 'Medicine deleted successfully'})
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'Cannot delete medicine with related purchases/sales'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Suppliers Endpoints
@app.route('/suppliers', methods=['GET'])
def get_suppliers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Suppliers")
        suppliers = cursor.fetchall()
        return jsonify(suppliers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Suppliers WHERE SupplierID = %s", (supplier_id,))
        supplier = cursor.fetchone()
        return jsonify(supplier) if supplier else ('', 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/suppliers', methods=['POST'])
def add_supplier():
    try:
        data = request.get_json()
        required_fields = ['Name', 'ContactNumber', 'Email', 'Address']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Suppliers (Name, ContactNumber, Email, Address)
            VALUES (%s, %s, %s, %s)
        """, (data['Name'], data['ContactNumber'], data['Email'], data['Address']))
        conn.commit()
        return jsonify({'message': 'Supplier added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Purchases Endpoints
@app.route('/purchases', methods=['GET'])
def get_purchases():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, s.Name AS SupplierName, m.Name AS MedicineName 
            FROM Purchases p
            JOIN Suppliers s ON p.SupplierID = s.SupplierID
            JOIN Medicines m ON p.MedicineID = m.MedicineID
        """)
        purchases = cursor.fetchall()
        return jsonify(purchases)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/purchases', methods=['POST'])
def add_purchase():
    try:
        data = request.get_json()
        required_fields = ['SupplierID', 'MedicineID', 'Quantity', 'PurchaseDate']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check Supplier and Medicine exist
        cursor.execute("SELECT SupplierID FROM Suppliers WHERE SupplierID = %s", (data['SupplierID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Supplier not found'}), 404
        cursor.execute("SELECT MedicineID FROM Medicines WHERE MedicineID = %s", (data['MedicineID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Medicine not found'}), 404

        # Insert purchase
        cursor.execute("""
            INSERT INTO Purchases (SupplierID, MedicineID, Quantity, PurchaseDate)
            VALUES (%s, %s, %s, %s)
        """, (data['SupplierID'], data['MedicineID'], data['Quantity'], data['PurchaseDate']))

        # Update medicine stock
        cursor.execute("""
            UPDATE Medicines SET Stock = Stock + %s WHERE MedicineID = %s
        """, (data['Quantity'], data['MedicineID']))

        # Log inventory change
        cursor.execute("""
            INSERT INTO InventoryLogs (MedicineID, ChangeType, QuantityChanged, Notes)
            VALUES (%s, 'Added', %s, %s)
        """, (data['MedicineID'], data['Quantity'], f"Purchase from supplier {data['SupplierID']}"))

        conn.commit()
        return jsonify({'message': 'Purchase added successfully'}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/purchases/<int:purchase_id>', methods=['DELETE'])
def delete_purchase(purchase_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get purchase details
        cursor.execute("SELECT MedicineID, Quantity FROM Purchases WHERE PurchaseID = %s", (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            return jsonify({'error': 'Purchase not found'}), 404

        # Delete purchase
        cursor.execute("DELETE FROM Purchases WHERE PurchaseID = %s", (purchase_id,))

        # Update stock
        cursor.execute("""
            UPDATE Medicines SET Stock = Stock - %s WHERE MedicineID = %s
        """, (purchase['Quantity'], purchase['MedicineID']))

        # Log inventory change
        cursor.execute("""
            INSERT INTO InventoryLogs (MedicineID, ChangeType, QuantityChanged, Notes)
            VALUES (%s, 'Removed', %s, %s)
        """, (purchase['MedicineID'], -purchase['Quantity'], f"Purchase {purchase_id} deleted"))

        conn.commit()
        return jsonify({'message': 'Purchase deleted successfully'})

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Sales Endpoints
@app.route('/sales', methods=['GET'])
def get_sales():
    try:
        limit = request.args.get('limit', default=None, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT s.*, c.Name AS CustomerName, m.Name AS MedicineName 
            FROM Sales s
            JOIN Customers c ON s.CustomerID = c.CustomerID
            JOIN Medicines m ON s.MedicineID = m.MedicineID
            ORDER BY s.SaleDate DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        sales = cursor.fetchall()
        return jsonify(sales)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/sales', methods=['POST'])
def add_sale():
    try:
        data = request.get_json()
        required_fields = ['CustomerID', 'MedicineID', 'Quantity', 'SaleDate']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check customer and medicine exist
        cursor.execute("SELECT CustomerID FROM Customers WHERE CustomerID = %s", (data['CustomerID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Customer not found'}), 404

        cursor.execute("SELECT Price, Stock FROM Medicines WHERE MedicineID = %s", (data['MedicineID'],))
        medicine = cursor.fetchone()
        if not medicine:
            return jsonify({'error': 'Medicine not found'}), 404

        # Check stock
        if medicine['Stock'] < data['Quantity']:
            return jsonify({'error': 'Insufficient stock'}), 400

        total_amount = medicine['Price'] * data['Quantity']

        # Insert sale
        cursor.execute("""
            INSERT INTO Sales (CustomerID, MedicineID, Quantity, SaleDate, TotalAmount)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['CustomerID'], data['MedicineID'], data['Quantity'], data['SaleDate'], total_amount))

        # Update stock
        cursor.execute("""
            UPDATE Medicines SET Stock = Stock - %s WHERE MedicineID = %s
        """, (data['Quantity'], data['MedicineID']))

        # Log inventory
        cursor.execute("""
            INSERT INTO InventoryLogs (MedicineID, ChangeType, QuantityChanged, Notes)
            VALUES (%s, 'Sold', %s, %s)
        """, (data['MedicineID'], -data['Quantity'], f"Sale to customer {data['CustomerID']}"))

        conn.commit()
        return jsonify({'message': 'Sale added successfully'}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/sales/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT MedicineID, Quantity FROM Sales WHERE SaleID = %s", (sale_id,))
        sale = cursor.fetchone()
        if not sale:
            return jsonify({'error': 'Sale not found'}), 404

        # Delete sale
        cursor.execute("DELETE FROM Sales WHERE SaleID = %s", (sale_id,))

        # Restore stock
        cursor.execute("""
            UPDATE Medicines SET Stock = Stock + %s WHERE MedicineID = %s
        """, (sale['Quantity'], sale['MedicineID']))

        # Log inventory
        cursor.execute("""
            INSERT INTO InventoryLogs (MedicineID, ChangeType, QuantityChanged, Notes)
            VALUES (%s, 'Added', %s, %s)
        """, (sale['MedicineID'], sale['Quantity'], f"Sale {sale_id} deleted"))

        conn.commit()
        return jsonify({'message': 'Sale deleted successfully'})

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Customers Endpoints
@app.route('/customers', methods=['GET'])
def get_customers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customers")
        customers = cursor.fetchall()
        return jsonify(customers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()
        return jsonify(customer) if customer else ('', 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        data = request.get_json()
        required_fields = ['Name', 'ContactNumber']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Customers (Name, ContactNumber, Email)
            VALUES (%s, %s, %s)
        """, (data['Name'], data['ContactNumber'], data.get('Email', '')))
        conn.commit()
        return jsonify({'message': 'Customer added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        fields = {
            'name': 'Name',
            'contact_number': 'ContactNumber',
            'email': 'Email'
        }

        for key, db_field in fields.items():
            if key in data:
                updates.append(f"{db_field} = %s")
                params.append(data[key])

        if not updates:
            return jsonify({'error': 'No fields to update'}), 400

        params.append(customer_id)
        cursor.execute(f"UPDATE Customers SET {', '.join(updates)} WHERE CustomerID = %s", params)
        conn.commit()
        return jsonify({'message': 'Customer updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Customers WHERE CustomerID = %s", (customer_id,))
        conn.commit()
        return jsonify({'message': 'Customer deleted successfully'})
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'Cannot delete customer with related records'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Employees Endpoints
@app.route('/employees', methods=['GET'])
def get_employees():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Employees")
        employees = cursor.fetchall()
        return jsonify(employees)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/employees', methods=['POST'])
def add_employee():
    try:
        data = request.get_json()
        required_fields = ['Name', 'Role', 'Salary', 'HireDate']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Employees (Name, Role, Salary, HireDate, ContactNumber)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['Name'],
            data['Role'],
            float(data['Salary']),
            data['HireDate'],
            data.get('ContactNumber', '')
        ))
        conn.commit()
        return jsonify({'message': 'Employee added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Doctors Endpoints
@app.route('/doctors', methods=['GET'])
def get_doctors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.*, COUNT(p.PrescriptionID) AS PrescriptionCount 
            FROM Doctors d
            LEFT JOIN Prescriptions p ON d.DoctorID = p.DoctorID
            GROUP BY d.DoctorID
        """)
        doctors = cursor.fetchall()
        return jsonify(doctors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/medicines/expiring-soon', methods=['GET'])
def get_expiring_medicines():
    try:
        threshold_days = int(request.args.get('threshold', 30))  # Default: 30 days
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM Medicines 
            WHERE ExpiryDate BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
        """, (threshold_days,))
        
        medicines = cursor.fetchall()
        return jsonify(medicines)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Doctors WHERE DoctorID = %s", (doctor_id,))
        conn.commit()
        return jsonify({'message': 'Doctor deleted successfully'})
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'Cannot delete doctor with existing prescriptions'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Prescriptions Endpoints
@app.route('/prescriptions', methods=['GET'])
def get_prescriptions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, d.Name AS DoctorName, c.Name AS CustomerName 
            FROM Prescriptions p
            JOIN Doctors d ON p.DoctorID = d.DoctorID
            JOIN Customers c ON p.CustomerID = c.CustomerID
        """)
        prescriptions = cursor.fetchall()
        return jsonify(prescriptions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/prescriptions', methods=['POST'])
def add_prescription():
    try:
        data = request.get_json()
        required_fields = ['DoctorID', 'CustomerID', 'DateIssued']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check doctor and customer exist
        cursor.execute("SELECT DoctorID FROM Doctors WHERE DoctorID = %s", (data['DoctorID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Doctor not found'}), 404
            
        cursor.execute("SELECT CustomerID FROM Customers WHERE CustomerID = %s", (data['CustomerID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Customer not found'}), 404

        cursor.execute("""
            INSERT INTO Prescriptions (DoctorID, CustomerID, DateIssued, Notes)
            VALUES (%s, %s, %s, %s)
        """, (
            data['DoctorID'],
            data['CustomerID'],
            data['DateIssued'],
            data.get('Notes', '')
        ))
        conn.commit()
        return jsonify({'message': 'Prescription added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# PrescriptionDetails Endpoints
@app.route('/prescription-details', methods=['GET'])
def get_prescription_details():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT pd.*, m.Name AS MedicineName, p.DateIssued 
            FROM PrescriptionDetails pd
            JOIN Medicines m ON pd.MedicineID = m.MedicineID
            JOIN Prescriptions p ON pd.PrescriptionID = p.PrescriptionID
        """)
        details = cursor.fetchall()
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/prescription-details', methods=['POST'])
def add_prescription_detail():
    try:
        data = request.get_json()
        required_fields = ['PrescriptionID', 'MedicineID', 'Dosage', 'Duration']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check prescription and medicine exist
        cursor.execute("SELECT PrescriptionID FROM Prescriptions WHERE PrescriptionID = %s", (data['PrescriptionID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Prescription not found'}), 404
            
        cursor.execute("SELECT MedicineID FROM Medicines WHERE MedicineID = %s", (data['MedicineID'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Medicine not found'}), 404

        cursor.execute("""
            INSERT INTO PrescriptionDetails (PrescriptionID, MedicineID, Dosage, Duration)
            VALUES (%s, %s, %s, %s)
        """, (
            data['PrescriptionID'],
            data['MedicineID'],
            data['Dosage'],
            data['Duration']
        ))
        conn.commit()
        return jsonify({'message': 'Prescription detail added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# InventoryLogs Endpoints
@app.route('/inventory-logs', methods=['GET'])
def get_inventory_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get filter parameters
        medicine_id = request.args.get('medicine_id')
        change_type = request.args.get('change_type')
        
        query = """
            SELECT il.*, m.Name AS MedicineName 
            FROM InventoryLogs il
            JOIN Medicines m ON il.MedicineID = m.MedicineID
        """
        params = []
        
        if medicine_id or change_type:
            query += " WHERE "
            conditions = []
            if medicine_id:
                conditions.append("il.MedicineID = %s")
                params.append(int(medicine_id))
            if change_type:
                conditions.append("il.ChangeType = %s")
                params.append(change_type)
            query += " AND ".join(conditions)
            
        cursor.execute(query, params)
        logs = cursor.fetchall()
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/inventory-logs/<int:log_id>', methods=['GET'])
def get_inventory_log(log_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT il.*, m.Name AS MedicineName 
            FROM InventoryLogs il
            JOIN Medicines m ON il.MedicineID = m.MedicineID
            WHERE il.LogID = %s
        """, (log_id,))
        log = cursor.fetchone()
        return jsonify(log) if log else ('', 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Customers, Employees, Doctors, Prescriptions, PrescriptionDetails, InventoryLogs endpoints follow similar patterns

if __name__ == '__main__':
    app.run(debug=True)