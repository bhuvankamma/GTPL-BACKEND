# app/crud.py
import json
import boto3
import os
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fpdf import FPDF

from database import get_db
from models.config import *

# ================= AWS =================
s3 = boto3.client("s3", region_name=AWS_REGION)
ses = boto3.client("ses", region_name=SES_REGION)

# ================= COMMON =================
def response(success, message=None, data=None, status=200, status_code=None):
    return {
        "success": success,
        "message": message,
        "data": data,
        "status": status or status_code
    }

def ensure_admin(user):
    role = str(user.get("role", "")).strip().upper()
    if role not in ("ADMIN", "HR"):
        raise Exception("Admin access required")


def ensure_employee(user):
    role = str(user.get("role", "")).strip().upper()
    if role not in ("EMPLOYEE", "CONTRACTOR"):
        raise Exception("Employee access required")



# BUSINESS HELPERS
# =====================================================

def calculate_lop(basic_salary, working_days, lop_days):
    if not basic_salary or not working_days or not lop_days:
        return 0
    return round((basic_salary / working_days) * lop_days, 2)

def months_elapsed(month):
    dt = datetime.strptime(month, "%B %Y")
    fy_start = datetime(dt.year if dt.month >= 4 else dt.year - 1, 4, 1)
    return (dt.year - fy_start.year) * 12 + (dt.month - fy_start.month) + 1

def get_financial_year(payroll_month):
    year = payroll_month.year
    return f"{year}-{year+1}" if payroll_month.month >= 4 else f"{year-1}-{year}"

def get_fy_date_range(financial_year: str):
    start_year, end_year = map(int, financial_year.split("-"))
    return (
        date(start_year, 4, 1),
        date(end_year, 3, 31)
    )
from decimal import Decimal

def json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    return value

def calculate_income_tax_115bac(annual_taxable_income: float) -> float:
    # Section 87A rebate (NEW regime)
    if annual_taxable_income <= 700000:
        return 0.0

    if annual_taxable_income <= 300000:
        tax = 0.0
    elif annual_taxable_income <= 600000:
        tax = (annual_taxable_income - 300000) * 0.05
    elif annual_taxable_income <= 900000:
        tax = 15000 + (annual_taxable_income - 600000) * 0.10
    elif annual_taxable_income <= 1200000:
        tax = 45000 + (annual_taxable_income - 900000) * 0.15
    elif annual_taxable_income <= 1500000:
        tax = 90000 + (annual_taxable_income - 1200000) * 0.20
    else:
        tax = 150000 + (annual_taxable_income - 1500000) * 0.30

    # surcharge (kept as you wrote — correct)
    if annual_taxable_income > 20000000:
        tax *= 1.25
    elif annual_taxable_income > 10000000:
        tax *= 1.15
    elif annual_taxable_income > 5000000:
        tax *= 1.10

    tax *= 1.04  # cess
    return round(tax, 2)    

def calculate_income_tax_old_regime(taxable_income: float) -> float:
    tax = 0.0

    if taxable_income <= 250000:
        tax = 0.0
    elif taxable_income <= 500000:
        tax = (taxable_income - 250000) * 0.05
    elif taxable_income <= 1000000:
        tax = 12500 + (taxable_income - 500000) * 0.20
    else:
        tax = 112500 + (taxable_income - 1000000) * 0.30

    tax *= 1.04  # cess
    return round(tax, 2)
    
# DATA FETCH 
######################################################

def fetch_tax_regime(emp_code, payroll_month):
    fy = get_financial_year(payroll_month)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT tax_regime, locked
        FROM employee_tax_regime
        WHERE emp_code = %s AND financial_year = %s
    """, (emp_code, fy))

    row = cur.fetchone()
    if not row:
        return "NEW", False   # default NEW regime

    return row[0], row[1]

def lock_tax_regime(emp_code, payroll_month):
    fy = get_financial_year(payroll_month)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE employee_tax_regime
        SET locked = TRUE
        WHERE emp_code = %s AND financial_year = %s
    """, (emp_code, fy))

    conn.commit()

def fetch_employee(emp_code):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.emp_code,
            e.first_name || ' ' || e.last_name AS full_name,
            e.designation,
            e.department,
            e.gender,
            e.location,
            e.dob,
            e.date_of_joining AS global_doj,
            e.basic_salary,
            e.variable_pay_percent,
            e.official_email AS email,
            e.status,

            s.bank_name,
            s.account_number,
            s.pan_number,
            s.pf_number,
            s.esi_number,
            s.epf_uan_ssn AS uan,

            p.pay_mode AS pay_mode,
            p.payroll_start_date,
            p.working_days,
            p.lop_days,
            p.previous_lop,
            p.lop_reversal

        FROM employees e
        LEFT JOIN employee_statutory s ON s.emp_code = e.emp_code
        LEFT JOIN employee_payslip p ON p.emp_code = e.emp_code
        WHERE e.emp_code = %s
    """, (emp_code,))

    row = cur.fetchone()
    if not row:
        return None

    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))

# LOSS OF PAY CALCULATION (CTC-BASED – REAL PAYROLL)
# =====================================================

def apply_lop_calculation(emp: dict):
    annual_ctc = emp.get("ctc") or 0
    monthly_gross = annual_ctc / 12 if annual_ctc else 0

    working_days = emp.get("working_days") or 0
    lop_days = emp.get("lop_days") or 0
    lop_reversal = emp.get("lop_reversal") or 0

    if monthly_gross > 0 and working_days > 0 and lop_days > 0:
        per_day_salary = monthly_gross / working_days
        lop_amount = round(per_day_salary * lop_days, 2)
    else:
        per_day_salary = 0
        lop_amount = 0.0

    lop_amount = max(lop_amount - lop_reversal, 0)

    emp["per_day_salary"] = round(per_day_salary, 2)
    emp["lop_amount"] = lop_amount

    return emp 

# =====================================================
# PDF

def build_payslip_pdf(emp: dict, month: str, breakup: dict) -> bytes:
    from fpdf import FPDF

    # ---------------- PAGE SETUP ----------------
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=9)

    # ---------------- COLUMN WIDTHS (A4 SAFE) ----------------
    W_EARN = 38
    W_STD = 22
    W_MON = 22
    W_YTD = 26
    W_DED = 38
    W_AMT = 22
    W_DYTD = 20
    LEFT_BLOCK = W_EARN + W_STD + W_MON + W_YTD
    RIGHT_BLOCK = W_DED + W_AMT + W_DYTD

# ---------------- HEADER (FINAL – RIGHT SIDE LOCKED) ----------------

    # Logo (LEFT ONLY)
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        LOGO_PATH = os.path.join(BASE_DIR, "utils", "wysele_logo.png")
        pdf.image(LOGO_PATH, x=10, y=20, w=32)
    except Exception:
        pass

    # RIGHT COLUMN (PRINT FIRST, LOCKED)
    RIGHT_X = 150
    RIGHT_W = 50

    pdf.set_xy(RIGHT_X, 20)
    pdf.set_font("Arial", size=9)
    pdf.cell(RIGHT_W, 5, f"Payslip for: {month}", align="R", ln=True)
    pdf.set_x(RIGHT_X)
    pdf.cell(RIGHT_W, 5, f"Amount in INR: {breakup['monthly']['Gross']:,.2f}", align="R", ln=True)

    # ---------------- CENTER BLOCK (ABSOLUTE, FIXED) ----------------

    CENTER_Y_START = 22

    pdf.set_font("Arial", "B", 13)
    pdf.set_xy(0, CENTER_Y_START)
    pdf.cell(210, 7, "WYSELE TECHNOLOGIES LLP", align="C")

    pdf.set_font("Arial", size=10)
    pdf.set_xy(0, CENTER_Y_START + 8)
    pdf.cell(210, 6, "308, Abacus IT Park,", align="C")

    pdf.set_xy(0, CENTER_Y_START + 14)
    pdf.cell(210, 6, "Uppal, Hyderabad-500039", align="C")

    # Space after header
    pdf.ln(10)


    # ---------------- EMPLOYEE INFO ----------------
    def val(k):
        v = emp.get(k)
        return "" if v is None else str(v)

    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(220, 220, 220)

    rows = [
        ("Employee Code", val("emp_code"), "Employee Name", val("full_name")),
        ("Designation", val("designation"), "Bank Name", val("bank_name")),
        ("Department", val("department"), "Account Number", val("account_number")),
        ("DOB", val("dob"), "PAN", val("pan_number")),
        ("PF Number", val("pf_number"), "Location", val("location")),
        ("India Payroll Start Date", val("payroll_start_date"), "ESIC No", val("esi_number")),
        ("Work Days", val("working_days"), "UAN", val("uan")),
        ("Previous LOP", val("previous_lop"), "LOP Days", val("lop_days")),
        ("Gender", val("gender"), "Global DOJ", val("global_doj")),
        ("LOP Reversal", val("lop_reversal"), "Regime Type", val("tax_regime")),
        ("", "", "PAY MODE", val("pay_mode")),
    ]

    for l1, v1, l2, v2 in rows:
        pdf.cell(45, 7, l1, 1, 0, fill=True)
        pdf.cell(45, 7, v1, 1)
        pdf.cell(45, 7, l2, 1, 0, fill=True)
        pdf.cell(45, 7, v2, 1)
        pdf.ln()

    pdf.ln(6)

    # ---------------- EARNINGS / DEDUCTIONS ----------------
    ytd_months = months_elapsed(month)

    earnings = [
        ("Basic Salary", breakup["monthly"]["Basic"]),
        ("House Rent Allowance", breakup["monthly"]["HRA"]),
        ("Special Allowance", breakup["monthly"]["Special Allowance"]),
        ("Variable Pay", breakup["monthly"]["Variable Pay"]),

    ]

    deductions = [
        ("Provident Fund", breakup["deductions"]["Provident Fund"]),
        ("Professional Tax", breakup["deductions"]["Professional Tax"]),
        ("Income Tax", breakup["deductions"]["Income Tax"]),
        ("Loss of Pay", breakup["deductions"]["Loss of Pay"]),

    ]

    pdf.set_font("Arial", "B", 9)
    pdf.cell(W_EARN, 8, "Earnings", 1, 0, "C", True)
    pdf.cell(W_STD, 8, "Standard", 1, 0, "C", True)
    pdf.cell(W_MON, 8, "Monthly", 1, 0, "C", True)
    pdf.cell(W_YTD, 8, "YTD Amount", 1, 0, "C", True)
    pdf.cell(W_DED, 8, "Deductions", 1, 0, "C", True)
    pdf.cell(W_AMT, 8, "Amount", 1, 0, "C", True)
    pdf.cell(W_DYTD, 8, "YTD", 1, 1, "C", True)

    pdf.set_font("Arial", size=9)

    gross = 0
    ded = 0
    max_rows = max(len(earnings), len(deductions))

    for i in range(max_rows):
        # ----- Earnings -----
        if i < len(earnings):
            e, a = earnings[i]
            gross += a
            pdf.cell(W_EARN, 8, e, 1)
            pdf.cell(W_STD, 8, f"{a:,.2f}", 1, 0, "R")
            pdf.cell(W_MON, 8, f"{a:,.2f}", 1, 0, "R")
            pdf.cell(W_YTD, 8, f"{a*ytd_months:,.2f}", 1, 0, "R")
        else:
            pdf.cell(LEFT_BLOCK, 8, "", 1)

        # ----- Deductions -----
        if i < len(deductions):
            d, a = deductions[i]
            ded += a
            pdf.cell(W_DED, 8, d, 1)
            pdf.cell(W_AMT, 8, f"{a:,.2f}", 1, 0, "R")
            pdf.cell(W_DYTD, 8, f"{a*ytd_months:,.2f}", 1, 1, "R")
        else:
            pdf.cell(RIGHT_BLOCK, 8, "", 1, 1)

    # ---------------- TOTALS ----------------
    pdf.set_font("Arial", "B", 9)
    pdf.cell(LEFT_BLOCK, 8, "Gross Pay", 1)
    pdf.cell(RIGHT_BLOCK, 8, f"{breakup['monthly']['Gross']:,.2f}", 1, 1, "R")

    # Gross Deduction
    pdf.cell(LEFT_BLOCK, 8, "Gross Deduction", 1)
    pdf.cell(RIGHT_BLOCK, 8, f"{breakup['deductions']['Total']:,.2f}", 1, 1, "R")

    # Net Pay
    pdf.cell(LEFT_BLOCK, 8, "Net Pay", 1)
    pdf.cell(RIGHT_BLOCK, 8, f"{breakup['net_pay']:,.2f}", 1, 1, "R")

    # ---------------- FOOTER ----------------
    pdf.set_y(-30)
    pdf.set_draw_color(220, 0, 0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.ln(4)
    pdf.set_font("Arial", size=8)
    pdf.multi_cell(
        0,
        5,
        "#308 4th Floor DSL Abacus IT Park, Uppal, Hyderabad, Telangana, 500039\n"
        "Phone: 040 45267773   Email: info@wysele.com   Web: www.wysele.com",
        align="C"
    )

    return pdf.output(dest="S").encode("latin-1")

def generate_form16_part_b(emp_code: str, financial_year: str):
    conn = get_db()
    cur = conn.cursor()

    fy_start, fy_end = get_fy_date_range(financial_year)

    # --------------------------------------------------
    # 1️⃣ Employee details
    # --------------------------------------------------
    emp = fetch_employee(emp_code)
    if not emp:
        raise Exception("Employee not found")

    # --------------------------------------------------
    # 2️⃣ Annual payroll aggregation
    # --------------------------------------------------
    cur.execute("""
        SELECT
            COALESCE(SUM(basic), 0),
            COALESCE(SUM(hra), 0),
            COALESCE(SUM(special_allowance), 0),
            COALESCE(SUM(variable_pay), 0),
            COALESCE(SUM(gross_pay), 0),
            COALESCE(SUM(employee_pf), 0),
            COALESCE(SUM(income_tax), 0)
        FROM payroll_monthly
        WHERE emp_code = %s
          AND payroll_month BETWEEN %s AND %s
    """, (emp_code, fy_start, fy_end))

    (
        total_basic,
        total_hra,
        total_special,
        total_variable,
        total_gross,
        total_employee_pf,
        total_tds
    ) = cur.fetchone()

    total_basic = Decimal(str(total_basic))
    total_hra = Decimal(str(total_hra))
    total_special = Decimal(str(total_special))
    total_variable = Decimal(str(total_variable))
    total_gross = Decimal(str(total_gross))
    total_employee_pf = Decimal(str(total_employee_pf))
    total_tds = Decimal(str(total_tds))

    # --------------------------------------------------
    # 3️⃣ Tax regime (locked at payroll time)
    # --------------------------------------------------
    cur.execute("""
        SELECT tax_regime
        FROM payroll_monthly
        WHERE emp_code = %s
          AND payroll_month BETWEEN %s AND %s
        LIMIT 1
    """, (emp_code, fy_start, fy_end))

    row = cur.fetchone()
    tax_regime = row[0] if row else "NEW"

    # --------------------------------------------------
    # 4️⃣ Standard deduction
    # --------------------------------------------------
    standard_deduction = Decimal("75000") if tax_regime == "NEW" else Decimal("50000")

    # --------------------------------------------------
    # 5️⃣ Taxable income
    # --------------------------------------------------
    taxable_income = (
    total_gross
    - standard_deduction
    - (total_employee_pf if tax_regime == "OLD" else Decimal("0"))
    )

    if taxable_income < Decimal("0"):
        taxable_income = Decimal("0")


    # --------------------------------------------------
    # 6️⃣ Annual tax recomputation (verification)
    # --------------------------------------------------
    if tax_regime == "OLD":
        annual_tax = Decimal(calculate_income_tax_old_regime(float(taxable_income)))
    else:
        annual_tax = Decimal(calculate_income_tax_115bac(float(taxable_income)))

    cess = (annual_tax * Decimal("0.04")).quantize(Decimal("0.01"))
    total_tax_liability = (annual_tax + cess).quantize(Decimal("0.01"))
    tax_balance = (total_tax_liability - total_tds).quantize(Decimal("0.01"))

    # --------------------------------------------------
    # 7️⃣ Final JSON (Form 16 Part B)
    # --------------------------------------------------
    form16_json = {
        "employee_details": {
            "emp_code": emp_code,
            "name": emp.get("full_name"),
            "pan": emp.get("pan_number"),
            "designation": emp.get("designation"),
            "department": emp.get("department"),
            "date_of_joining": str(emp.get("global_doj")),
            "financial_year": financial_year
        },

        "salary_breakup": {
            "basic": json_safe(total_basic),
            "hra": json_safe(total_hra),
            "special_allowance": json_safe(total_special),
            "variable_pay": json_safe(total_variable),
            "gross_salary": json_safe(total_gross)
        },

        "exemptions": {
            "hra_exempted": 0,
            "lta": 0,
            "other_exemptions": 0,
            "total_exemptions": 0
        },

        "standard_deduction": {
            "amount": json_safe(standard_deduction)
        },


        "other_income": {
            "interest_from_savings": 0,
            "interest_from_fd": 0,
            "other_income_total": 0
        },

        "deductions": {
            "section_80c": {
                "employee_pf": json_safe(total_employee_pf),
                "other_80c": 0,
                "total_80c": json_safe(total_employee_pf)
            },
            "section_80d": 0,
            "total_deductions": json_safe(total_employee_pf)
        },


        "tax_calculation": {
            "gross_total_income": json_safe(total_gross),
            "standard_deduction": json_safe(standard_deduction),
            "total_deductions": json_safe(total_employee_pf if tax_regime == "OLD" else Decimal("0")),
            "taxable_income": json_safe(taxable_income),
            "income_tax": json_safe(annual_tax),
            "cess": json_safe(cess),
            "total_tax_liability": json_safe(total_tax_liability)
        },

        "tds_details": {
            "total_tds_deducted": json_safe(total_tds),
            "months": 12
        },

        "final_numbers": {
            "tax_payable": json_safe(total_tax_liability),
            "tax_deducted": json_safe(total_tds),
            "tax_balance": json_safe(tax_balance)
        },


        "pdf_meta": {
            "generated_on": str(date.today()),
            "generated_by": "SYSTEM",
            "document_type": "FORM_16_PART_B"
        }
    }

    # --------------------------------------------------
    # 8️⃣ Store Form 16 Part B
    # --------------------------------------------------
    cur.execute("""
        INSERT INTO form16_part_b (emp_code, financial_year, json_data)
        VALUES (%s, %s, %s)
        ON CONFLICT (emp_code, financial_year)
        DO UPDATE SET
            json_data = EXCLUDED.json_data,
            generated_at = NOW()
    """, (emp_code, financial_year, json.dumps(form16_json)))

    conn.commit()

    return form16_json

# ACTIONS
# =====================================================

def build_salary_from_employee(emp: dict):
    # --------------------------------------------------
    # Annual & Monthly Salary
    # --------------------------------------------------
    annual_ctc = Decimal(emp["basic_salary"])
    monthly_ctc = annual_ctc / Decimal("12")

    # Deductions : 
    STD_DEDUCTION_OLD = Decimal("50000")
    STD_DEDUCTION_NEW = Decimal("75000")  # FY 2025–26

    # --------------------------------------------------
    # Variable Pay (Bonus)
    # --------------------------------------------------
    variable_percent = Decimal(emp.get("variable_pay_percent", 0))
    annual_variable = annual_ctc * variable_percent / Decimal("100")
    monthly_variable = annual_variable / Decimal("12")

    fixed_monthly = monthly_ctc - monthly_variable

    # --------------------------------------------------
    # Earnings Structure
    
    basic = (annual_ctc * Decimal("0.50")) / Decimal("12")
    hra = basic * Decimal("0.40")

    # Remaining salary as Special Allowance
    special = fixed_monthly - (basic + hra)
    gross_monthly = basic + hra + special + monthly_variable
    annual_gross_salary = gross_monthly * Decimal("12")

    # --------------------------------------------------
    # PF (Employee Contribution – capped)
    # --------------------------------------------------
    # Employee PF – deduction
    employee_pf = basic * Decimal("0.12")

    # Employer PF – company cost (CTC component)
    employer_pf = basic * Decimal("0.12")

    # --------------------------------------------------
    # Other deductions
    # --------------------------------------------------
    professional_tax = Decimal("200")
    emp = apply_lop_calculation(emp)
    lop_amount = Decimal(emp.get("lop_amount", 0))

    # --------------------------------------------------
    # TAX REGIME NORMALIZATION (🔥 CRITICAL FIX 🔥)
    # --------------------------------------------------
    raw_regime = emp.get("tax_regime", "NEW")

    tax_regime = str(raw_regime).strip().upper()
    if tax_regime in ("OLD", "OLD REGIME", "OLD_TAX", "O"):
        tax_regime = "OLD"
    else:
        tax_regime = "NEW"

    regime_type = tax_regime

    # --------------------------------------------------
    # TAXABLE INCOME (ANNUAL)
    # --------------------------------------------------
    if tax_regime == "OLD":
        taxable_income = (
        annual_gross_salary
        - STD_DEDUCTION_OLD
        - (employee_pf * Decimal("12"))
        )
    else:  # NEW regime
        taxable_income = (
            annual_gross_salary
            - STD_DEDUCTION_NEW
        )

    if taxable_income < 0:
        taxable_income = Decimal("0")

    # --------------------------------------------------
    # Annual Income Tax
    # --------------------------------------------------
    if tax_regime == "OLD":
        annual_tax = Decimal(
            calculate_income_tax_old_regime(float(taxable_income))
        )
    else:
        annual_tax = Decimal(
            calculate_income_tax_115bac(float(taxable_income))
        )

    # --------------------------------------------------
    # Monthly TDS (spread over remaining months)
    # --------------------------------------------------
    months_remaining = Decimal(emp.get("months_remaining", 12))
    monthly_income_tax = (
        annual_tax / months_remaining
        if months_remaining > 0
        else Decimal("0")
    )

    # --------------------------------------------------
    # Monthly deductions
    # --------------------------------------------------
    total_deductions = (
        employee_pf
        + professional_tax
        + monthly_income_tax
        + lop_amount
    )

    net_pay = gross_monthly - total_deductions

    # --------------------------------------------------
    # Formatter
    # --------------------------------------------------
    def money(val):
        return float(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    # --------------------------------------------------
    # Final Output
    # --------------------------------------------------
    return {
        "ctc_annual": money(annual_ctc),
        "Regime_type":tax_regime,

        "pf": {
            "employee_pf": money(employee_pf),
            "employer_pf": money(employer_pf),
        },


        "monthly": {
            "Basic": money(basic),
            "HRA": money(hra),
            "Special Allowance": money(special),
            "Variable Pay": money(monthly_variable),
            "Gross": money(gross_monthly),
        },

        "deductions": {
            "Provident Fund": money(employee_pf),
            "Professional Tax": money(professional_tax),
            "Income Tax": money(monthly_income_tax),
            "Loss of Pay": money(lop_amount),
            "Total": money(total_deductions),
        },

        "net_pay": money(net_pay),
    }    


def action_select_tax_regime(payload, user):
    # -----------------------------
    # 1️⃣ Identity (from users)
    # -----------------------------
    emp_code = user.get("emp_code")
    if not emp_code:
        return response(False, "Unauthorized", 401)

    # -----------------------------
    # 2️⃣ Ensure employee exists
    # -----------------------------
    emp = fetch_employee(emp_code)
    if not emp:
        return response(False, "Employee record not found", 404)

    # -----------------------------
    # 3️⃣ Validate input
    # -----------------------------
    tax_regime = payload.get("tax_regime")
    financial_year = payload.get("financial_year")

    if tax_regime not in ("OLD", "NEW"):
        return response(False, "Invalid tax regime", 400)

    # -----------------------------
    # 4️⃣ One-time per FY
    # -----------------------------
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT locked
        FROM employee_tax_regime
        WHERE emp_code=%s AND financial_year=%s
    """, (emp_code, financial_year))

    row = cur.fetchone()
    if row and row[0]:
        return response(
            False,
            "Tax regime already locked for this financial year",
            403
        )

    # -----------------------------
    # 5️⃣ Insert / Update
    # -----------------------------
    cur.execute("""
        INSERT INTO employee_tax_regime (emp_code, financial_year, tax_regime)
        VALUES (%s,%s,%s)
        ON CONFLICT (emp_code, financial_year)
        DO UPDATE SET
            tax_regime=EXCLUDED.tax_regime,
            selected_at=NOW()
    """, (emp_code, financial_year, tax_regime))

    conn.commit()

    return response(True, "Tax regime selected successfully")


def generate_monthly_payslip(emp_code, payroll_month, user):
    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ Fetch employee profile (NO tax regime here)
    emp = fetch_employee(emp_code)
    if not emp:
        raise Exception("Employee not found")

    # 2️⃣ Fetch tax regime from employee_tax_regime table
    tax_regime, locked = fetch_tax_regime(emp_code, payroll_month)

    # 🔥 Inject tax regime into emp dict for salary calculation
    emp["tax_regime"] = tax_regime

    # 3️⃣ Calculate salary (unchanged logic)
    salary = build_salary_from_employee(emp)

    # 4️⃣ Insert / Update payroll
    cur.execute("""
        INSERT INTO payroll_monthly (
            emp_code, payroll_month,
            basic, hra, special_allowance, variable_pay,
            gross_pay,
            employee_pf, employer_pf,
            professional_tax, income_tax,
            total_deductions, net_pay,
            tax_regime,
            generated_by_role,
            generated_by_emp_code,
            generated_at
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        ON CONFLICT (emp_code, payroll_month)
        DO UPDATE SET
            basic = EXCLUDED.basic,
            hra = EXCLUDED.hra,
            special_allowance = EXCLUDED.special_allowance,
            variable_pay = EXCLUDED.variable_pay,
            gross_pay = EXCLUDED.gross_pay,
            employee_pf = EXCLUDED.employee_pf,
            employer_pf = EXCLUDED.employer_pf,
            professional_tax = EXCLUDED.professional_tax,
            income_tax = EXCLUDED.income_tax,
            total_deductions = EXCLUDED.total_deductions,
            net_pay = EXCLUDED.net_pay,
            tax_regime = EXCLUDED.tax_regime,
            generated_by_role = EXCLUDED.generated_by_role,
            generated_by_emp_code = EXCLUDED.generated_by_emp_code,
            generated_at = NOW()
    """, (
        emp_code,
        payroll_month,
        salary["monthly"]["Basic"],
        salary["monthly"]["HRA"],
        salary["monthly"]["Special Allowance"],
        salary["monthly"].get("Variable Pay", 0),
        salary["monthly"]["Gross"],
        salary["pf"]["employee_pf"],
        salary["pf"]["employer_pf"],
        salary["deductions"]["Professional Tax"],
        salary["deductions"]["Income Tax"],
        salary["deductions"]["Total"],
        salary["net_pay"],
        tax_regime,                 # 🔥 from new table
        user["role"],
        user.get("emp_code")
    ))

    conn.commit()

    # 5️⃣ Lock tax regime AFTER first successful generation
    if not locked:
        lock_tax_regime(emp_code, payroll_month)

    return salary 

def send_email(to_email, subject, body):
    print("📧 send_email() called")
    print("📧 TO:", to_email)
    print("📧 SUBJECT:", subject)

    response = ses.send_email(
        Source=SES_SOURCE_EMAIL,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": body}}
        }
    )

    print("📧 SES RESPONSE:", response)

def action_request_payslip(payload, user):
    emp_code = user.get("emp_code")
    month = payload.get("month")
    year = payload.get("year")

    if not emp_code or not month or not year:
        return response(False, "emp_code, month and year are required", 400)

    MONTH_MAP = {
        "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3,
        "APRIL": 4, "MAY": 5, "JUNE": 6,
        "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9,
        "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12
    }

    month_num = MONTH_MAP.get(month.upper())
    if not month_num:
        return response(False, "Invalid month", 400)

    requested_month_date = date(year, month_num, 1)
    current_month_date = date.today().replace(day=1)

    if requested_month_date > current_month_date:
        return response(False, "Cannot request payslip for future month", 400)

    conn = get_db()
    cur = conn.cursor()

    # 🔍 Check employee status
    cur.execute("""
        SELECT status
        FROM employees
        WHERE emp_code = %s
    """, (emp_code,))
    row = cur.fetchone()

    if not row:
        return response(False, "Employee record not found", 404)

    status = str(row[0]).upper()
    if status != "ACTIVE":
        return response(False, "Employee is not active", 403)

    # 🔁 Check if payslip already generated
    cur.execute("""
        SELECT 1
        FROM salary_structures
        WHERE emp_code = %s
          AND month = %s
    """, (emp_code, f"{month} {year}"))

    if cur.fetchone():
        return response(
            False,
            "Payslip already generated. Please download it.",
            409
        )

    # 🔁 Check existing request
    cur.execute("""
        SELECT 1
        FROM payslip_requests
        WHERE emp_code = %s
          AND month = %s
          AND year = %s
          AND status IN ('PENDING', 'APPROVED')
    """, (emp_code, month, year))

    if cur.fetchone():
        return response(
            False,
            "Payslip request already exists for this month",
            409
        )

    # ✅ Insert request
    cur.execute("""
        INSERT INTO payslip_requests (emp_code, month, year, status)
        VALUES (%s, %s, %s, 'PENDING')
    """, (emp_code, month, year))

    conn.commit()

    return response(True, "Payslip request submitted successfully")


def action_generate(payload, user):
    ensure_admin(user)

    emp_code = payload["emp_code"]
    month = payload["month"]
    year = payload["year"]

    MONTH_MAP = {
        "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3,
        "APRIL": 4, "MAY": 5, "JUNE": 6,
        "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9,
        "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12
    }

    month_num = MONTH_MAP.get(month.upper())
    if not month_num:
        return response(False, "Invalid month", status_code=400)

    payroll_month = date(year, month_num, 1)

    # 1️⃣ Fetch employee FIRST
    emp = fetch_employee(emp_code)
    if not emp:
        return response(False, "Employee not found", status_code=404)

    status = str(emp.get("status", "")).upper()
    if status != "ACTIVE":
        return response(
            False,
            f"Payslip cannot be generated. Employee status is {emp.get('status')}",
            status_code=400
        )

    # 2️⃣ Generate payroll (DB insert/update)
    breakup = generate_monthly_payslip(
        emp_code=emp_code,
        payroll_month=payroll_month,
        user=user
    )

    # 3️⃣ Generate PDF
    pdf_bytes = build_payslip_pdf(
        emp=emp,
        month=f"{month} {year}",
        breakup=breakup
    )

    # 4️⃣ Upload to S3
    s3_key = f"payslip/{emp_code}/{month}_{year}.pdf"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=pdf_bytes,
        ContentType="application/pdf"
    )

    # 5️⃣ Store payslip reference
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO salary_structures (emp_code, month, s3_key)
        VALUES (%s, %s, %s)
        ON CONFLICT (emp_code, month)
        DO UPDATE SET
            s3_key = EXCLUDED.s3_key,
            generated_at = NOW()
    """, (emp_code, f"{month} {year}", s3_key))
    conn.commit()

    # 6️⃣ Email employee
    email = emp.get("email")
    if email:
        try:
            signed_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET, "Key": s3_key},
                ExpiresIn=86400
            )

            send_email(
                to_email=official_email,
                subject=f"Payslip – {month} {year}",
                body=f"""Hello {emp.get('full_name')},

Your payslip for {month} {year} has been generated.

Download your payslip:
{signed_url}

Regards,
HR Team
"""
            )
        except Exception as e:
            print("EMAIL ERROR:", str(e))
    else:
        print(f"WARNING: No email found for emp_code={emp_code}")

    return response(
        True,
        "Payslip generated successfully",
        {
            "emp_code": emp_code,
            "month": f"{month} {year}",
            "s3_key": s3_key
        }
    )




def action_generate_bulk(payload, user):
    ensure_admin(user)

    month = payload.get("month")
    year = payload.get("year")
    emp_codes = payload.get("emp_codes")

    if not month or not year:
        return response(False, "Month and year required", 400)

    conn = get_db()
    cur = conn.cursor()

    if not emp_codes:
        cur.execute("""
            SELECT emp_code
            FROM employees
            WHERE status = 'ACTIVE';
        """)
        emp_codes = [r[0] for r in cur.fetchall()]

    success = []
    failed = []

    for emp_code in emp_codes:
        try:
            action_generate(
                payload={
                    "emp_code": emp_code,
                    "month": month,
                    "year": year
                },
                user=user
            )
            success.append(emp_code)
        except Exception as e:
            failed.append({
                "emp_code": emp_code,
                "error": str(e)
            })

    return response(True, "Bulk payslip generation completed", {
        "generated_count": len(success),
        "failed_count": len(failed),
        "generated": success,
        "failed": failed
    })

def action_list_payslip_requests(user):
    ensure_admin(user)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            r.id,
            r.emp_code,
            e.first_name || ' ' || e.last_name AS employee_name,
            r.month,
            r.year,
            r.status,
            r.requested_at
        FROM payslip_requests r
        JOIN employees e ON e.emp_code = r.emp_code
        ORDER BY r.requested_at DESC
    """)

    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    return response(True, data=[dict(zip(cols, r)) for r in rows])

def action_approve_payslip_request(payload, user):
    ensure_admin(user)

    emp_code = payload.get("emp_code")
    month = payload.get("month")
    year = payload.get("year")

    if not emp_code or not month or not year:
        return response(False, "emp_code, month and year are required", 400)

    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ Ensure pending request exists
    cur.execute("""
        SELECT 1
        FROM payslip_requests
        WHERE emp_code=%s AND month=%s AND year=%s AND status='PENDING'
    """, (emp_code, month, year))

    if not cur.fetchone():
        return response(False, "No pending request found", 404)

    # 2️⃣ Approve request
    cur.execute("""
        UPDATE payslip_requests
        SET
            status='APPROVED',
            approved_by_emp_code=%s,
            approved_at=NOW()
        WHERE emp_code=%s AND month=%s AND year=%s
    """, (
        user["emp_code"],
        emp_code,
        month,
        year
    ))

    conn.commit()

    # 3️⃣ Generate payslip
    try:
        action_generate(
            {"emp_code": emp_code, "month": month, "year": year},
            user
        )
    except Exception as e:
        return response(False, f"Approved but generation failed: {str(e)}", 500)

    return response(True, "Payslip approved and generated successfully")



def action_reject_payslip_request(payload, user):
    ensure_admin(user)

    emp_code = payload.get("emp_code")
    month = payload.get("month")
    year = payload.get("year")
    reason = payload.get("reason", "Rejected by admin")

    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ Ensure pending request exists
    cur.execute("""
        SELECT 1
        FROM payslip_requests
        WHERE emp_code=%s AND month=%s AND year=%s AND status='PENDING'
    """, (emp_code, month, year))

    if not cur.fetchone():
        return response(False, "No pending request found", 404)

    # 2️⃣ Reject request
    cur.execute("""
        UPDATE payslip_requests
        SET
            status='REJECTED',
            remarks=%s,
            approved_by_emp_code=%s,
            approved_at=NOW()
        WHERE emp_code=%s AND month=%s AND year=%s
    """, (
        reason,
        user["emp_code"],
        emp_code,
        month,
        year
    ))

    conn.commit()
    return response(True, "Payslip request rejected successfully")



def action_my_payslip_requests(user):
    ensure_employee(user)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, month, year, status, requested_at, approved_at
        FROM payslip_requests
        WHERE emp_code = %s
        ORDER BY requested_at DESC
    """, (user["emp_code"],))

    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    return response(True, data=[dict(zip(cols, r)) for r in rows])

def action_download_payslip(payload, user):
    conn = get_db()
    cur = conn.cursor()

    emp_code = payload["emp_code"]
    month = payload["month"]
    year = payload["year"]

    user_emp_code = user.get("emp_code")
    user_role = user.get("role")  # may be None

    # 🔐 Authorization
    if user_emp_code != emp_code:
        if user_role not in ("ADMIN", "HR"):
            return response(False, "Access denied", 403)

    month_year = f"{month} {year}"

    cur.execute("""
        SELECT s3_key
        FROM salary_structures
        WHERE emp_code = %s
          AND month = %s
    """, (emp_code, month_year))

    row = cur.fetchone()
    if not row:
        return response(False, "Payslip not found", 404)

    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": row[0]},
        ExpiresIn=86400
    )

    return response(True, data={"download_url": url})


def action_generate_form16_part_b(payload, user):
    ensure_admin(user)  # only ADMIN / HR

    emp_code = payload.get("emp_code")
    financial_year = payload.get("financial_year")

    if not emp_code or not financial_year:
        return response(False, "emp_code and financial_year are required", 400)

    try:
        form16_json = generate_form16_part_b(emp_code, financial_year)
        return response(
            True,
            "Form 16 Part B generated successfully",
            form16_json
        )
    except Exception as e:
        return response(False, str(e), 500)