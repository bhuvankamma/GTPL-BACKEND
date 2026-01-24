from fastapi import Header, HTTPException, status
from database import get_db

def get_current_user(x_emp_code: str = Header(None)):
    # 1️⃣ Header validation
    if not x_emp_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-EMP-CODE header missing"
        )

    emp_code = x_emp_code.strip().upper()

    # 2️⃣ Fetch user from USERS table
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT emp_code, role, status
        FROM users
        WHERE emp_code = %s
    """, (emp_code,))

    row = cur.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user"
        )

    user = {
        "emp_code": row[0],
        "role": row[1],
        "status": row[2]
    }

    # 3️⃣ Normalize (CRITICAL)
    user["emp_code"] = str(user["emp_code"]).strip().upper()
    user["role"] = str(user["role"]).strip().upper()

    # 4️⃣ Block inactive users
    if user["status"] != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    return user
