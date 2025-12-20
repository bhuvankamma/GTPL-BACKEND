import pyodbc
import hashlib
import smtplib
import random
import secrets # NEW: For generating secure, hard-to-guess tokens
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# NOTE: Base URL is where your React app (or Flask) will handle the link click.
BASE_FRONTEND_URL = 'http://localhost:3000/reset-password/' 


# ----------------- Utilities -----------------
def hash_password(password):
    """Hashes the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_secure_token():
    """Generates a secure, URL-safe password reset token."""
    # Using 32 bytes gives a string about 43 characters long, which is safe for NVARCHAR(128)
    return secrets.token_urlsafe(32)

# ----------------------------------------------------
# >>> FINAL CONNECTION FIX: Connect to Default Instance (MSSQLSERVER) <<<
def get_connection():
    """Establishes a connection to the SQL Server Default Instance (MSSQLSERVER)."""
    connection_string = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost;'
        'DATABASE=UserDB2;'
        'Trusted_Connection=yes;'
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except pyodbc.Error as e:
        sql_error = str(e)
        print("!! CRITICAL DATABASE CONNECTION FAILED !!")
        print(f"Error Details: {sql_error}")
        return None 

# ----------------------------------------------------

def send_email(email, subject, body):
    """General function to send emails (used for OTP and Reset Link)."""
    sender = "chandinisahasra02@gmail.com"
    # !!! IMPORTANT: UPDATE THIS PASSWORD WITH YOUR NEW GMAIL APP PASSWORD !!!
    password = "eoxxyqhscrsqhsyk" 
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, email, msg.as_string())
        server.quit()
        print(f"Email sent to {email} with subject: {subject}")
        return {"success": True, "message": f"{subject} sent successfully."}
    except smtplib.SMTPAuthenticationError:
        print("Failed to send email: SMTP Authentication Error (Incorrect App Password).")
        return {"success": False, "message": "SMTP Authentication Error: Check App Password."}
    except Exception as e:
        print(f"Failed to send email (General Error): {type(e).__name__}: {e}")
        return {"success": False, "message": f"Failed to send email: {type(e).__name__}"}

def send_otp(email, otp):
    """Sends the one-time password (OTP) via email."""
    subject = "Your Registration OTP Verification Code"
    body = f"Your OTP code for registration is: {otp}. It is valid for 10 minutes."
    return send_email(email, subject, body)


# ----------------- Helper: Find User Table by Email or ID -----------------

def find_user_table(identifier):
    """
    Checks which table (Admins, Employees, or Employers) the identifier (email or ID) belongs to.
    Returns: Tuple of (table_name, identifier_type, actual_email) or None
    """
    if identifier is None:
        return None 

    conn = get_connection()
    if conn is None: return None
    
    cursor = conn.cursor()
    try:
        # Check all tables to find the user and their email
        tables = {"Admins": "email", "Employees": "employee_id", "Employers": "employer_id"}
        
        for table, id_col in tables.items():
            col_name = "email" if "@" in identifier else id_col 

            # For Admins, always search by email
            if table == "Admins" and col_name != "email": continue

            cursor.execute(f"SELECT email, password FROM dbo.{table} WHERE {col_name}=?", (identifier,))
            record = cursor.fetchone()
            
            if record:
                id_type = "email" if "@" in identifier else id_col
                # Also return the hashed password for reuse in the update function
                return table, id_type, record[0], record[1] # Return Table, Identifier Type, Actual Email, Hashed Password
            
    finally:
        if conn:
            conn.close()
            
    return None

# ----------------- Registration -----------------
# (Registration logic remains the same)
def register_user(role, identifier=None, full_name=None, email=None, password=None, phone=None, department=None, company=None):
    conn = get_connection()
    if conn is None:
        return {"success": False, "message": "Registration failed: Could not connect to the database."}

    cursor = conn.cursor()
    role_map = {"Admin": "Admins", "Employee": "Employees", "Employer": "Employers"}
    table = role_map.get(role)
    if not table:
        return {"success": False, "message": "Invalid role!"}

    try:
        # Check for existing email across all tables (essential check)
        for tbl in role_map.values():
            cursor.execute(f"SELECT email FROM dbo.{tbl} WHERE email=?", (email,))
            if cursor.fetchone():
                return {"success": False, "message": f"Email {email} already registered."}

        hashed_pwd = hash_password(password)
        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=10)
        
        # We reuse otp_code/otp_expiry for the registration OTP
        if role == "Admin":
            cursor.execute("INSERT INTO dbo.Admins (full_name, company_name, email, password, phone_number, is_verified, otp_code, otp_expiry) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (full_name, company, email, hashed_pwd, phone, 0, otp, expiry))
        elif role == "Employee":
            cursor.execute("INSERT INTO dbo.Employees (employee_id, full_name, email, password, phone_number, department, is_verified, otp_code, otp_expiry) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (identifier, full_name, email, hashed_pwd, phone, department, 0, otp, expiry))
        elif role == "Employer":
            cursor.execute("INSERT INTO dbo.Employers (employer_id, company_name, email, password, phone_number, department, is_verified, otp_code, otp_expiry) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (identifier, company, email, hashed_pwd, phone, department, 0, otp, expiry))

        conn.commit()
        send_otp(email, otp)
        return {"success": True, "message": "Registration complete. Check email for OTP verification."}
    except Exception as e:
        print(f"Error in registration: {e}")
        return {"success": False, "message": f"Database error during registration: {e}"}
    finally:
        if conn:
            conn.close()


# ----------------- OTP Verification -----------------
# (OTP Verification logic remains the same)
def verify_user(email, otp_input):
    """Verifies the user's OTP code and activates the account if successful."""
    # Find user info, but we only need the table name and email
    user_info = find_user_table(email)
    if not user_info:
        return {"success": False, "message": "User not found or database connection failed!"}
    
    table, _, user_email, _ = user_info # Table name, email
    
    conn = get_connection()
    if conn is None: return {"success": False, "message": "Could not connect to the database."}
    
    cursor = conn.cursor()
    try:
        # Ensure we query using 'email'
        cursor.execute(f"SELECT otp_code, otp_expiry FROM dbo.{table} WHERE email=? AND is_verified=0", (user_email,))
        record = cursor.fetchone()

        if not record:
            return {"success": False, "message": "No pending verification or already verified."}

        otp_code, otp_expiry = record

        if datetime.now() > otp_expiry:
            return {"success": False, "message": "OTP expired. Please request registration again."}

        if otp_code == otp_input:
            # Clear OTP fields on success
            cursor.execute(f"UPDATE dbo.{table} SET is_verified=1, otp_code=NULL, otp_expiry=NULL WHERE email=?", (user_email,))
            conn.commit()
            return {"success": True, "message": f"Email {user_email} verified successfully!"}
        else:
            return {"success": False, "message": "Invalid OTP!"}

    except Exception as e:
        print(f"Error in OTP verification: {e}")
        return {"success": False, "message": f"Server error during verification: {e}"}
    finally:
        if conn:
            conn.close()


# ----------------- Login -----------------
# (Login logic remains the same)
def login_user(identifier, password):
    """
    Authenticates the user using either email or ID as the identifier.
    Returns: {"success": True, "message": ..., "user_role": "Admins/Employees/Employers"}
    """
    # NOTE: find_user_table now returns (table, id_type, actual_email, hashed_pwd)
    user_info = find_user_table(identifier) 
    if not user_info:
        return {"success": False, "message": "Invalid credentials or user not found."}
        
    table, id_type, user_email, stored_hashed_pwd = user_info

    conn = get_connection()
    if conn is None: return {"success": False, "message": "Could not connect to the database."}
    
    cursor = conn.cursor()
    try:
        # Determine which column to query against
        query_col = "email"
        if table in ["Employees", "Employers"] and id_type != "email":
            query_col = f"{table[:-1].lower()}_id" # employee_id or employer_id
        
        # Select the necessary fields (Name/Company, Password, Verification Status)
        if table == "Admins":
            select_col = "full_name"
        elif table == "Employees":
            select_col = "full_name"
        elif table == "Employers":
            select_col = "company_name"
            
        # We already have the hashed password from find_user_table, only need verification status now
        cursor.execute(f"SELECT {select_col}, is_verified FROM dbo.{table} WHERE {query_col}=?", (identifier,))
        user_data = cursor.fetchone()

        if not user_data:
            return {"success": False, "message": "Invalid credentials or user not found."}

        name_or_company, is_verified = user_data

        if not is_verified:
            return {"success": False, "message": "Account not verified. Please complete OTP verification first."}

        if hash_password(password) == stored_hashed_pwd:
            # IMPORTANT: Return the user_role which maps directly to the table name
            return {"success": True, "message": f"Welcome {name_or_company}!", "user_role": table, "user_email": user_email}
        else:
            return {"success": False, "message": "Invalid credentials or user not found."}

    except Exception as e:
        print(f"Error in login: {e}")
        return {"success": False, "message": f"Server error during login: {e}"}
    finally:
        if conn:
            conn.close()


# ----------------- NEW: Forgot Password (Link-Based) -----------------

def forgot_password_link(identifier):
    """Generates a secure token and sends a password reset link to the user's email."""
    # NOTE: user_info now returns (table, id_type, actual_email, stored_hashed_pwd)
    user_info = find_user_table(identifier) 
    if not user_info:
        return {"success": False, "message": "User not found."}
        
    table, id_type, user_email, _ = user_info

    conn = get_connection()
    if conn is None: return {"success": False, "message": "Could not connect to the database."}
    
    cursor = conn.cursor()
    try:
        # 1. Generate and save the secure token
        token = generate_secure_token()
        expiry = datetime.now() + timedelta(hours=1) 

        # Determine which column to query against
        query_col = "email" if id_type == "email" else f"{table[:-1].lower()}_id" 
        
        # We reuse otp_code for the token and otp_expiry for the token expiry
        cursor.execute(f"""
            UPDATE dbo.{table} 
            SET otp_code=?, otp_expiry=? 
            WHERE {query_col}=?
        """, (token, expiry, identifier))
        conn.commit()

        # 2. Prepare and send the verification link email
        reset_link = f"{BASE_FRONTEND_URL}?token={token}" # Changed to use query parameter
        subject = "Password Reset Request"
        body = f"""
        You requested a password reset for your account.
        Please click the link below to set a new password:
        
        {reset_link}
        
        This link is valid for 1 hour. If you did not request this, please ignore this email.
        """
        
        email_result = send_email(user_email, subject, body)
        
        if email_result.get('success'):
            return {"success": True, "message": f"A password reset link has been sent to {user_email}. Check your inbox."}
        else:
            return {"success": False, "message": f"Password reset email failed to send. Please contact support."}

    except Exception as e:
        print(f"Error in forgot password link: {e}")
        return {"success": False, "message": f"Server error during password reset request: {e}"}
    finally:
        if conn:
            conn.close()

# ----------------- NEW: FINAL PASSWORD UPDATE FUNCTION -----------------

def update_password_with_token(token, old_password, new_password):
    """
    Final step: Validates the token, checks the old password, and updates the new password.
    
    FIXES:
    1. Accepts (token, old_password, new_password) to match app.py.
    2. Contains full validation logic (token, expiry, old password check).
    3. Uses explicit SQL parameterization to avoid syntax errors.
    """
    conn = get_connection()
    if conn is None: 
        return {"success": False, "message": "Could not connect to the database."}
    
    cursor = conn.cursor()
    try:
        tables = ["Admins", "Employees", "Employers"]
        user_info = None

        # 1. Find user by token across all tables and check token validity
        for table in tables:
            # Query for the user that has the token
            cursor.execute(f"SELECT email, password, otp_expiry FROM dbo.{table} WHERE otp_code=?", (token,))
            record = cursor.fetchone()
            
            if record:
                user_email, stored_hashed_pwd, token_expiry = record
                
                if datetime.now() > token_expiry:
                    # Token found but expired - clear it
                    cursor.execute(f"UPDATE dbo.{table} SET otp_code=NULL, otp_expiry=NULL WHERE email=?", (user_email,))
                    conn.commit()
                    return {"success": False, "message": "Password reset link has expired. Please request a new one."}
                
                # Token is valid, store info and break loop
                user_info = {"table": table, "email": user_email, "stored_hashed_pwd": stored_hashed_pwd}
                break

        if not user_info:
            return {"success": False, "message": "Invalid or already used password reset link."}
        
        table = user_info['table']
        user_email = user_info['email']
        stored_hashed_pwd = user_info['stored_hashed_pwd']
        
        # 2. Check Old Password
        if hash_password(old_password) != stored_hashed_pwd:
            return {"success": False, "message": "The Old Password you entered is incorrect."}
            
        # 3. Check New Password against Old
        new_hashed_pwd = hash_password(new_password)
        if new_hashed_pwd == stored_hashed_pwd:
            return {"success": False, "message": "The New Password cannot be the same as the Old Password."}

        # 4. Update password and clear token fields
        cursor.execute(f"""
            UPDATE dbo.{table} 
            SET password=?, otp_code=NULL, otp_expiry=NULL 
            WHERE email=?
        """, (new_hashed_pwd, user_email))
        conn.commit()
        
        return {"success": True, "message": "Password updated successfully! You can now log in with your new password."}

    except pyodbc.Error as e:
        sql_error = str(e)
        print(f"Error in password update (SQL): {sql_error}")
        # The SQL syntax error is still caught here if it persists!
        return {"success": False, "message": f"Server error during password update (SQL): {sql_error}"}
    except Exception as e:
        print(f"Error in password update (General): {e}")
        return {"success": False, "message": f"Server error during password update: {e}"}
    finally:
        if conn:
            conn.close()


# ----------------- Utility Functions (Verification) -----------------
# (Logic remains the same)
def verify_reset_token(token):
    """
    Verifies a password reset token. 
    NOTE: This is now largely redundant but kept for any old calls.
    The main logic is in the final update function now.
    """
    conn = get_connection()
    if conn is None: return {"success": False, "message": "Could not connect to the database."}
    
    cursor = conn.cursor()
    try:
        tables = ["Admins", "Employees", "Employers"]
        current_time = datetime.now()
        
        for table in tables:
            cursor.execute(f"SELECT email, otp_expiry FROM dbo.{table} WHERE otp_code=?", (token,))
            record = cursor.fetchone()
            
            if record:
                user_email, token_expiry = record
                
                if current_time > token_expiry:
                    cursor.execute(f"UPDATE dbo.{table} SET otp_code=NULL, otp_expiry=NULL WHERE email=?", (user_email,))
                    conn.commit()
                    return {"success": False, "message": "Password reset link has expired. Please request a new one."}
                
                return {"success": True, "table": table, "email": user_email}
                
        return {"success": False, "message": "Invalid or already used password reset link."}

    except Exception as e:
        print(f"Error in token verification: {e}")
        return {"success": False, "message": f"Server error during token verification: {e}"}
    finally:
        if conn:
            conn.close()