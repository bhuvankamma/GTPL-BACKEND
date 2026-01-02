from fastapi import APIRouter, HTTPException
from db import get_cursor
from utils.id_card_pdf import generate_id_card

router = APIRouter()

@router.get("/employees/{employee_code}/id-card")
def get_employee_id_card(employee_code: str):
    conn, cur = get_cursor()

    try:
        # 1️⃣ Check if employee exists and fetch basic details
        cur.execute("""
            SELECT emp_code, first_name
            FROM employees
            WHERE emp_code = %s
        """, (employee_code,))
        employee_row = cur.fetchone()

        if not employee_row:
            raise HTTPException(status_code=404, detail="Employee not found")

        employee = {
            "emp_code": employee_row[0],
            "first_name": employee_row[1]
        }

        # 2️⃣ Check if ID card already exists
        cur.execute("""
            SELECT document_url, uploaded_at
            FROM employee_documents
            WHERE emp_code = %s
              AND document_type = 'ID_CARD'
            ORDER BY uploaded_at DESC
            LIMIT 1
        """, (employee_code,))
        doc = cur.fetchone()

        if doc and doc[0]:
            return {
                "status": "ID_CARD_EXISTS",
                "document_url": doc[0],
                "uploaded_at": doc[1]
            }

        # 3️⃣ Create ID card DB record if not exists
        if not doc:
            cur.execute("""
                INSERT INTO employee_documents (emp_code, document_type)
                VALUES (%s, 'ID_CARD')
            """, (employee_code,))
            conn.commit()

        # 4️⃣ Generate ID card PDF locally
        pdf_path = generate_id_card(employee)

        # 5️⃣ Update DB with generated PDF path
        cur.execute("""
            UPDATE employee_documents
            SET document_url = %s,
                uploaded_at = NOW()
            WHERE emp_code = %s
              AND document_type = 'ID_CARD'
        """, (pdf_path, employee_code))
        conn.commit()

        return {
            "status": "ID_CARD_PDF_GENERATED",
            "file_path": pdf_path
        }

    finally:
        cur.close()
        conn.close()
