from flask import Blueprint,Flask, request, jsonify
from flask_mail import Mail, Message
import pyodbc
import random
from db_connection import get_db_connection


log_bp = Blueprint("log", __name__)
#ddyj csxp iuhn wcns
mail = Mail()

# Store OTPs temporarily (in production, use a database or Redis)
otp_storage = {}

# Signup API
@log_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not firstname or not lastname or not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Generate a 6-digit OTP
        otp = random.randint(100000, 999999)
        otp_storage[email] = otp  # Store OTP temporarily

        # Send OTP to the user's email
        msg = Message('Your OTP for Signup', sender='sliitresearchmail@gmail.com', recipients=[email])
        msg.body = f'Your OTP for signup is: {otp}'
        mail.send(msg)

        return jsonify({"message": "OTP sent to your email"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# Verify OTP and Signup API
@log_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    otp = data.get('otp')
    username = data.get('username')
    password = data.get('password')

    print(f"Received data: {data}")  # Debugging line

    if not email or not otp or not username or not password:
        return jsonify({"error": "Email, OTP, username, and password are required"}), 400

    # Check if the OTP matches
    if email in otp_storage and otp_storage[email] == int(otp):
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Call the SignupUser stored procedure
            cursor.execute("EXEC SignupUser @FirstName=?,@LastName=?, @Username=?, @Email=?, @Password=?", firstname,lastname,username, email, password)
            conn.commit()

            # Remove the OTP from storage
            del otp_storage[email]

            return jsonify({"message": "Signup successful"}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({"error": "Invalid OTP"}), 400

# ReGenerate OTP
@log_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # Remove old OTP if it exists
    if email in otp_storage:
        del otp_storage[email]
        
    # Generate new OTP
    otp = random.randint(100000, 999999)
    otp_storage[email] = otp

    # Send OTP to the user's email
    try:
        msg = Message('Your OTP for Signup', sender='sliitresearchmail@gmail.com', recipients=[email])
        msg.body = f'Your new OTP is: {otp}'
        mail.send(msg)
    except Exception as e:
        return jsonify({"error": f"Failed to send OTP email: {str(e)}"}), 500
    
    return jsonify({"message": "OTP sent successfully"}), 200

# Login API
@log_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Call the LoginUser stored procedure
        cursor.execute("EXEC LoginUser @Username=?, @Password=?", username, password)
        user = cursor.fetchone()

        if user:
            return jsonify({
                "message": "Login successful",
                "user": {
                    "patientID": user.PatientID,
                    "username": user.Username
                }
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# Forgot Password API
@log_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Generate a 6-digit OTP
        otp = random.randint(100000, 999999)
        otp_storage[email] = otp  # Store OTP temporarily

        # Send OTP to the user's email
        msg = Message('Your OTP for Password Reset', sender='sliitresearchmail@gmail.com', recipients=[email])
        msg.body = f'Your OTP for Password Reset is: {otp}'
        mail.send(msg)

        return jsonify({"message": "OTP sent to your email"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

# Reset Password API
@log_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    password = data.get('password')

    if not email or not otp or not password:
        return jsonify({"error": "Email, OTP, and password are required"}), 400

    # Safely compare OTP
    if email in otp_storage and str(otp_storage[email]) == str(otp):
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Securely call the stored procedure
            cursor.execute("EXEC ResetPassword @Email=?, @Password=?", (email, password))
            conn.commit()

            # Remove used OTP
            del otp_storage[email]

            return jsonify({"message": "Password reset successful"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        finally:
            cursor.close()
            conn.close()

    else:
        return jsonify({"error": "Invalid OTP"}), 400

    
# Log Out API
@log_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logout successful"}), 200 





# Error Handler
@log_bp.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Resource not found"}), 404

# Error Handler
@log_bp.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# Error Handler
@log_bp.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

# Error Handler
@log_bp.errorhandler(400) # Bad Request
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400

# Error Handler
@log_bp.errorhandler(401) # Unauthorized
def unauthorized(e):
    return jsonify({"error": "Unauthorized"}), 401

# Error Handler
@log_bp.errorhandler(403) # Forbidden
def forbidden(e):
    return jsonify({"error": "Forbidden"}), 403

