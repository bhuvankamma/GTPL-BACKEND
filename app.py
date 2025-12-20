# app.py

from flask import Flask, request, jsonify 
# >>> REQUIRED IMPORT TO FIX CORS ERROR <<<
from flask_cors import CORS 

# Import the functions from your logic file (auth_service.py)
# -------------------- UPDATED IMPORTS --------------------
from auth_service import ( 
    register_user, 
    verify_user, 
    login_user, 
    forgot_password_link,       # <-- Sends the secure link
    verify_reset_token,         # <-- Validates the token from the link
    update_password_with_token  # <-- Updates password after token is validated
)
# ---------------------------------------------------------

# Initialize Flask app
app = Flask(__name__)

# ----------------------------------------------------------------------
# >>> CORS CONFIGURATION <<<
# This allows your React frontend (on a different port) to talk to your Flask backend
CORS(app) 
# ----------------------------------------------------------------------

# --- API Endpoints (Routes for the Frontend) ---

@app.route('/api/register', methods=['POST'])
def handle_register():
    """Handles user registration and sends OTP (Registration remains OTP-based)."""
    data = request.get_json()
    
    # Call the registration function 
    result = register_user(
        role=data.get('role'),
        identifier=data.get('identifier'),
        full_name=data.get('full_name'),
        email=data.get('email'),
        password=data.get('password'),
        phone=data.get('phone'),
        department=data.get('department'),
        company=data.get('company')
    )
    
    # Check for errors in database connection or registration
    if not result or not result.get('success', False):
        return jsonify(result or {"success": False, "message": "Registration failed due to server error."}), 400
    
    # Respond to the frontend with success status
    return jsonify(result), 200

# ----------------------------------------------------------------------

@app.route('/api/verify-otp', methods=['POST'])
def handle_verify():
    """Handles OTP submission for account verification (Registration remains OTP-based)."""
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    result = verify_user(email, otp)
    
    if not result or not result.get('success', False):
        return jsonify(result or {"success": False, "message": "Verification failed."}), 400
        
    return jsonify(result), 200

# ----------------------------------------------------------------------

@app.route('/api/login', methods=['POST'])
def handle_login():
    """Handles user login."""
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')
    
    result = login_user(identifier, password) 
    
    if not result or not result.get('success', False):
        return jsonify(result or {"success": False, "message": "Invalid email/ID or password."}), 401
    
    return jsonify(result), 200

# ----------------------------------------------------------------------
# ----------------- SECURE PASSWORD RESET FLOW -------------------------
# ----------------------------------------------------------------------

@app.route('/api/forgot-password', methods=['POST'])
def handle_forgot_password_link():
    """Step 1: Initiates password reset by sending a secure link to the user's email."""
    data = request.get_json()
    identifier = data.get('identifier') or data.get('email') 
    
    if not identifier:
        return jsonify({"success": False, "message": "Email/ID is missing from the request."}), 400

    result = forgot_password_link(identifier)

    if not result or not result.get('success', False):
        return jsonify(result or {"success": False, "message": "Failed to send reset link. User not found or server error."}), 400

    return jsonify(result), 200

# ----------------------------------------------------------------------

@app.route('/api/verify-reset-token', methods=['POST'])
def handle_verify_reset_token():
    """Step 2: Validates the secure token when the user loads the reset form."""
    data = request.get_json()
    token = data.get('token')
    
    result = verify_reset_token(token) 
    
    if not result or not result.get('success', False):
        return jsonify(result or {"success": False, "message": "Invalid or expired reset link."}), 400

    return jsonify(result), 200

# ----------------------------------------------------------------------

@app.route('/api/reset-password-final', methods=['POST']) # <--- *** CORRECTED ENDPOINT NAME ***
def handle_final_password_update():
    """
    Step 3: Updates the user's password using the token, new password, and old password.
    This endpoint name matches the hardcoded fetch URL in your React frontend.
    """
    data = request.get_json()
    
    token = data.get('token')
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')

    if not token or not old_password or not new_password:
        return jsonify({"success": False, "message": "Missing required fields for password update (token, oldPassword, or newPassword)."}), 400
    
    # NOTE: You MUST update the update_password_with_token function in auth_service.py 
    # to accept and validate the token, check the old_password against the stored hash, 
    # and only then update the new_password.
    
    # Passing the three required variables to your service function:
    result = update_password_with_token(token, old_password, new_password)
    
    if not result or not result.get('success', False):
        return jsonify(result or {"success": False, "message": "Password update failed. Invalid token, token expired, or new password matches old password."}), 400

    return jsonify(result), 200


if __name__ == '__main__':
    
    app.run(debug=True, port=5000)