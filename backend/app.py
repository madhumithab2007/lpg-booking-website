from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import datetime
import random

app = Flask(__name__)
CORS(app)

# ==================== DATABASE CONNECTION ====================
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='madhusam',  # CHANGE THIS TO YOUR PASSWORD
            database='lpg_booking_db'
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

# ==================== TEST ROUTE ====================
@app.route('/')
def home():
    return jsonify({'message': 'LPG Booking API is running!'})

# ==================== GET CYLINDERS ====================
@app.route('/api/cylinders', methods=['GET'])
def get_cylinders():
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cylinders")
    cylinders = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(cylinders), 200

# ==================== REGISTER USER ====================
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (full_name, email, phone, address, password) VALUES (%s, %s, %s, %s, %s)",
            (data['full_name'], data['email'], data['phone'], data['address'], data['password'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    except mysql.connector.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== LOGIN USER ====================
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (data['email'], data['password'])
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                'user_id': user['user_id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'user_type': user['user_type']
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== CREATE BOOKING ====================
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        
        booking_number = f"LPG{datetime.datetime.now().strftime('%Y%m%d')}{random.randint(1000,9999)}"
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO bookings (booking_number, user_id, cylinder_id, delivery_address, preferred_delivery_date) 
               VALUES (%s, %s, %s, %s, %s)""",
            (booking_number, data['user_id'], data['cylinder_id'], data['delivery_address'], data['preferred_delivery_date'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Booking created successfully', 'booking_number': booking_number}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== GET USER BOOKINGS ====================
@app.route('/api/bookings/user', methods=['GET'])
def get_user_bookings():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, c.type, c.weight_kg, c.price 
            FROM bookings b
            JOIN cylinders c ON b.cylinder_id = c.cylinder_id
            WHERE b.user_id = %s
            ORDER BY b.booking_date DESC
        """, (user_id,))
        bookings = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(bookings), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== CANCEL BOOKING ====================
@app.route('/api/bookings/<int:booking_id>/cancel', methods=['PUT'])
def cancel_booking(booking_id):
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check if booking exists and can be cancelled
        cursor.execute("SELECT status FROM bookings WHERE booking_id = %s", (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Booking not found'}), 404
        
        # Only pending or confirmed bookings can be cancelled
        if booking['status'] not in ['pending', 'confirmed']:
            cursor.close()
            conn.close()
            return jsonify({'error': f'Cannot cancel booking with status: {booking["status"]}'}), 400
        
        # Update status to cancelled
        cursor.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
            (booking_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Booking cancelled successfully'}), 200
        
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)