from fastapi import APIRouter, HTTPException
from db import get_cursor

router = APIRouter()

@router.get("/employees/{employee_code}/id-card")
def get_employee_id_card(employee_code: str):
    conn, cur = get_cursor()

    try:
        # 1️⃣ Check if employee exists
        cur.execute(
            "SELECT emp_code FROM employees WHERE emp_code = %s",
            (employee_code,)
        )
        employee = cur.fetchone()

        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # 2️⃣ Check if ID card already exists
        cur.execute("""
            SELECT file_path, created_at
            FROM employee_documents
            WHERE employee_code = %s
              AND document_type = 'ID_CARD'
            ORDER BY created_at DESC
            LIMIT 1
        """, (employee_code,))

        doc = cur.fetchone()

        if doc:
            return {
                "status": "ID_CARD_EXISTS",
                "file_path": doc[0],
                "created_at": doc[1]
            }

        # 3️⃣ If not generated yet
        return {
            "status": "ID_CARD_NOT_GENERATED"
        }

    finally:
        cur.close()
        conn.close()
