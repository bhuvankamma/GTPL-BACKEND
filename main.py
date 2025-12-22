import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# --------------------------------------------------
# CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
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


# ==================================================
# ================= EMPLOYEES ======================
# ==================================================

class EmployeeCreate(BaseModel):
    emp_code: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    password: str
    status: Optional[str] = "Active"


@app.post("/employees")
def create_employee(emp: EmployeeCreate):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            INSERT INTO employees
            (emp_code, first_name, last_name, email, department, password, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            emp.emp_code,
            emp.first_name,
            emp.last_name,
            emp.email,
            emp.department,
            emp.password,
            emp.status
        ))
        conn.commit()
        return {"status": "employee_created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ==================================================
# ================= ASSETS (UPDATED) ===============
# ==================================================

class AssetBase(BaseModel):
    asset_name: str
    category: str
    status: str
    description: Optional[str] = None
    assigned_emp_id: Optional[str] = None
    assigned_emp_name: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class Asset(AssetBase):
    id: int


@app.get("/assets", response_model=List[Asset])
def get_assets():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT id, asset_name, category, status, description,
                   assigned_emp_id, assigned_emp_name
            FROM assets
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "asset_name": r[1],
                "category": r[2],
                "status": r[3],
                "description": r[4],
                "assigned_emp_id": r[5],
                "assigned_emp_name": r[6],
            }
            for r in rows
        ]
    finally:
        cur.close()
        conn.close()


@app.post("/assets")
def create_asset(asset: AssetCreate):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            INSERT INTO assets
            (asset_name, category, status, description, assigned_emp_id, assigned_emp_name)
            VALUES (%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            asset.asset_name,
            asset.category,
            asset.status,
            asset.description,
            asset.assigned_emp_id,
            asset.assigned_emp_name
        ))
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id, "status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.put("/assets/{asset_id}")
def update_asset(asset_id: int, asset: AssetCreate):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            UPDATE assets
            SET asset_name=%s,
                category=%s,
                status=%s,
                description=%s,
                assigned_emp_id=%s,
                assigned_emp_name=%s
            WHERE id=%s
        """, (
            asset.asset_name,
            asset.category,
            asset.status,
            asset.description,
            asset.assigned_emp_id,
            asset.assigned_emp_name,
            asset_id
        ))
        conn.commit()
        return {"status": "updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int):
    conn, cur = get_cursor()
    try:
        cur.execute("DELETE FROM assets WHERE id=%s", (asset_id,))
        conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ==================================================
# ================= LEAVE ==========================
# ==================================================

class LeaveApprove(BaseModel):
    leave_id: int


@app.post("/leave/approve")
def approve_leave(data: LeaveApprove):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            UPDATE leave_requests
            SET status='Approved'
            WHERE id=%s
        """, (data.leave_id,))
        conn.commit()
        return {"status": "leave_approved"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ==================================================
# ================= ANNOUNCEMENTS ==================
# ==================================================

class AnnouncementCreate(BaseModel):
    title: str
    message: str


@app.post("/announcements")
def create_announcement(data: AnnouncementCreate):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            INSERT INTO announcements (title, message)
            VALUES (%s,%s)
        """, (data.title, data.message))
        conn.commit()
        return {"status": "announcement_created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ==================================================
# ================= DASHBOARD ======================
# ==================================================

@app.get("/dashboard/total-employees")
def total_employees():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM employees")
        return {"total_employees": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()


@app.get("/dashboard/present-today")
def present_today():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM attendance
            WHERE date = CURRENT_DATE
              AND status='Present'
        """)
        return {"present_today": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()


@app.get("/dashboard/on-leave")
def on_leave():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM leave_requests
            WHERE status='Approved'
              AND CURRENT_DATE BETWEEN start_date AND end_date
        """)
        return {"on_leave": cur.fetchone()[0]}
    finally:
        cur.close()
        conn.close()


@app.get("/dashboard/attendance-summary")
def attendance_summary():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT status, COUNT(*)
            FROM attendance
            WHERE date = CURRENT_DATE
            GROUP BY status
        """)
        return {row[0].lower(): row[1] for row in cur.fetchall()}
    finally:
        cur.close()
        conn.close()


@app.get("/dashboard/department-strength")
def department_strength():
    conn, cur = get_cursor()
    try:
        cur.execute("""
            SELECT department, COUNT(*)
            FROM employees
            GROUP BY department
        """)
        return [{"department": r[0], "count": r[1]} for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


# ==================================================
# ================= REWARDS ========================
# ==================================================

@app.post("/rewards")
def rewards(data: dict):
    conn, cur = get_cursor()
    try:
        cur.execute("""
            INSERT INTO job_work
            (job_title, hours_spent, description, employee_name)
            VALUES (%s, 0, %s, %s)
        """, (
            data.get("reward_title"),
            data.get("reward_title"),
            data.get("emp_code")
        ))
        conn.commit()
        return {"status": "reward_added"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()