from fastapi import APIRouter, HTTPException
from database_B import get_db_conn
from models.config_form12bb import DEFAULT_USER_ID
from datetime import datetime


router = APIRouter(prefix="/declaration", tags=["Declaration"])

# ==================================================
# POST : CREATE / UPDATE DECLARATION (UPSERT)
# ==================================================

from pydantic import BaseModel
from typing import Optional
class DeclarationRequest(BaseModel):
    emp_code: str
    financial_year: str  # ✅ REQUIRED
    current_monthly_rent: float = 0
    landlord_name: Optional[str] = None
    landlord_address: Optional[str] = None
    hra_amount: float = 0
    section_80c: float = 0
    section_80ccd: float = 0
    section_80d: float = 0
    section_80dd: float = 0
    section_80ddb: float = 0
    section_80e: float = 0
    section_80ee: float = 0
    section_80g: float = 0
    section_80u: float = 0
    section_80eea: float = 0
    section_80eeb: float = 0
    section_80tta: float = 0
    section_80ttb: float = 0
    home_loan_interest: float = 0
    lta_amount: float = 0

class DeclarationResponse(BaseModel):
    id: int
    emp_code: str
    financial_year: str
    current_monthly_rent: float
    landlord_name: Optional[str]
    landlord_address: Optional[str]
    hra_amount: float
    section_80c: float
    section_80ccd: float
    section_80d: float
    section_80dd: float
    section_80ddb: float
    section_80e: float
    section_80ee: float
    section_80g: float
    section_80u: float
    section_80eea: float
    section_80eeb: float
    section_80tta: float
    section_80ttb: float
    home_loan_interest: float
    lta_amount: float
    created_at: datetime
    updated_at: datetime

@router.post("/", response_model=DeclarationResponse)
def save_declaration(payload: DeclarationRequest ):
    fy = payload.financial_year
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM employees WHERE emp_code = %s",
            (payload.emp_code,)
        )
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail="Invalid emp_code")

        cur.execute(
            """
            INSERT INTO declarations (
                emp_code,
                financial_year,
                current_monthly_rent,
                landlord_name,
                landlord_address,
                hra_amount,
                section_80c,
                section_80ccd,
                section_80d,
                section_80dd,
                section_80ddb,
                section_80e,
                section_80ee,
                section_80g,
                section_80u,
                section_80eea,
                section_80eeb,
                section_80tta,
                section_80ttb,
                home_loan_interest,
                lta_amount
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (emp_code, financial_year)
            DO UPDATE SET
                current_monthly_rent = EXCLUDED.current_monthly_rent,
                landlord_name = EXCLUDED.landlord_name,
                landlord_address = EXCLUDED.landlord_address,
                hra_amount = EXCLUDED.hra_amount,
                section_80c = EXCLUDED.section_80c,
                section_80ccd = EXCLUDED.section_80ccd,
                section_80d = EXCLUDED.section_80d,
                section_80dd = EXCLUDED.section_80dd,
                section_80ddb = EXCLUDED.section_80ddb,
                section_80e = EXCLUDED.section_80e,
                section_80ee = EXCLUDED.section_80ee,
                section_80g = EXCLUDED.section_80g,
                section_80u = EXCLUDED.section_80u,
                section_80eea = EXCLUDED.section_80eea,
                section_80eeb = EXCLUDED.section_80eeb,
                section_80tta = EXCLUDED.section_80tta,
                section_80ttb = EXCLUDED.section_80ttb,
                home_loan_interest = EXCLUDED.home_loan_interest,
                lta_amount = EXCLUDED.lta_amount,
                updated_at = NOW()
            RETURNING
    id,
    emp_code,
    financial_year,
    current_monthly_rent,
    landlord_name,
    landlord_address,
    hra_amount,
    section_80c,
    section_80ccd,
    section_80d,
    section_80dd,
    section_80ddb,
    section_80e,
    section_80ee,
    section_80g,
    section_80u,
    section_80eea,
    section_80eeb,
    section_80tta,
    section_80ttb,
    home_loan_interest,
    lta_amount,
    created_at,
    updated_at

            """,
            (
                payload.emp_code,
                payload.financial_year,          # ✅ FIXED
                payload.current_monthly_rent,
                payload.landlord_name,
                payload.landlord_address,
                payload.hra_amount,
                payload.section_80c,
                payload.section_80ccd,
                payload.section_80d,
                payload.section_80dd,
                payload.section_80ddb,
                payload.section_80e,
                payload.section_80ee,
                payload.section_80g,
                payload.section_80u,
                payload.section_80eea,
                payload.section_80eeb,
                payload.section_80tta,
                payload.section_80ttb,
                payload.home_loan_interest,
                payload.lta_amount,
            )
        )

        row = cur.fetchone()   # ✅ defined here
        conn.commit()

        return {
            "id": row[0],
            "emp_code": row[1],
            "financial_year": row[2],
            "current_monthly_rent": row[3],
            "landlord_name": row[4],
            "landlord_address": row[5],
            "hra_amount": row[6],
            "section_80c": row[7],
            "section_80ccd": row[8],
            "section_80d": row[9],
            "section_80dd": row[10],
            "section_80ddb": row[11],
            "section_80e": row[12],
            "section_80ee": row[13],
            "section_80g": row[14],
            "section_80u": row[15],
            "section_80eea": row[16],
            "section_80eeb": row[17],
            "section_80tta": row[18],
            "section_80ttb": row[19],
            "home_loan_interest": row[20],
            "lta_amount": row[21],
            "created_at": row[22],
            "updated_at": row[23],
        }


    finally:
        conn.close()

# ==================================================
# GET : FETCH DECLARATION BY FINANCIAL YEAR
# ==================================================
@router.get("/")
def get_declaration(emp_code: str, fy: str):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                emp_code,
                financial_year,
                current_monthly_rent,
                landlord_name,
                landlord_address,
                hra_amount,
                section_80c,
                section_80ccd,
                section_80d,
                section_80dd,
                section_80ddb,
                section_80e,
                section_80ee,
                section_80g,
                section_80u,
                section_80eea,
                section_80eeb,
                section_80tta,
                section_80ttb,
                home_loan_interest,
                lta_amount,
                created_at,
                updated_at
            FROM declarations
            WHERE emp_code = %s AND financial_year = %s
            LIMIT 1
            """,
            (emp_code, fy)
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Declaration not found")

        return {
            "id": row[0],
            "emp_code": row[1],           # ✅ STRING
            "financial_year": row[2],
            "current_monthly_rent": row[3],
            "landlord_name": row[4],
            "landlord_address": row[5],
            "hra_amount": row[6],
            "section_80c": row[7],
            "section_80ccd": row[8],
            "section_80d": row[9],
            "section_80dd": row[10],
            "section_80ddb": row[11],
            "section_80e": row[12],
            "section_80ee": row[13],
            "section_80g": row[14],
            "section_80u": row[15],
            "section_80eea": row[16],
            "section_80eeb": row[17],
            "section_80tta": row[18],
            "section_80ttb": row[19],
            "home_loan_interest": row[20],
            "lta_amount": row[21],
            "created_at": row[22],
            "updated_at": row[23],
        }
    finally:
        conn.close()
