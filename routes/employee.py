from fastapi import APIRouter, HTTPException
from db import get_cursor
from utils.id_card_pdf import generate_id_card
from utils.s3_client import upload_file_to_s3
import os

router = APIRouter()

@router.get("/employees/{employee_code}/id-card")
def get_employee_id_card(employee_code: str):
    conn, cur = get_cursor()

    try:
        # 1️⃣ Fetch employee
        cur.execute("""
            SELECT emp_code, first_name
            FROM employees
            WHERE emp_code = %s
        """, (employee_code,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Employee not found")

        employee = {
            "emp_code": row[0],
            "first_name": row[1]
        }

        # 2️⃣ Check existing document
        cur.execute("""
            SELECT document_url, uploaded_at
            FROM employee_documents
            WHERE emp_code = %s
              AND document_type = 'ID_CARD'
            LIMIT 1
        """, (employee_code,))
        doc = cur.fetchone()

        if doc and doc[0]:
            return {
                "status": "ID_CARD_EXISTS",
                "document_url": doc[0],
                "uploaded_at": doc[1]
            }

        # 3️⃣ Ensure DB record
        if not doc:
            cur.execute("""
                INSERT INTO employee_documents (emp_code, document_type)
                VALUES (%s, 'ID_CARD')
            """, (employee_code,))
            conn.commit()

        # 4️⃣ Generate PDF locally
        local_pdf_path = generate_id_card(employee)

        # 5️⃣ Upload to S3
        s3_key = f"id_cards/{employee_code}.pdf"
        s3_url = upload_file_to_s3(local_pdf_path, s3_key)

        # 6️⃣ Save S3 URL
        cur.execute("""
            UPDATE employee_documents
            SET document_url = %s,
                uploaded_at = NOW()
            WHERE emp_code = %s
              AND document_type = 'ID_CARD'
        """, (s3_url, employee_code))
        conn.commit()

        return {
            "status": "ID_CARD_PDF_GENERATED",
            "document_url": s3_url
        }

    finally:
        cur.close()
        conn.close()
