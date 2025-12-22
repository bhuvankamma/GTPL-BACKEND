import psycopg2
from fastapi import HTTPException

def get_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            port=5432,
            database="hrms_crm",
            user="hrms_user",
            password="Loveudad43#",
            connect_timeout=5
        )
    except Exception as e:
        print("DB ERROR:", e)
        return None


def get_cursor():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return conn, conn.cursor()
