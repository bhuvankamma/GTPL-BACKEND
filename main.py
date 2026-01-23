from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from sqlalchemy.orm import Session

# DB helpers
from db import get_cursor, get_db

# Routers
from routes.candidate_evaluation import router as candidate_router
from routes.employee import router as employee_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router

from crud import employee_profile_edit

#======================================================
#Employee Tracking
#======================================================

import time
from collections import Counter
from typing import Optional

from fastapi import (
    FastAPI,
    Depends,
    Form,
    WebSocket,
    WebSocketDisconnect,
    Query
)
from sqlalchemy.orm import Session
from sqlalchemy import text

from database_su import get_db
from crud.employee_tracking_websocket_manager import ConnectionManager
from utils.Employee_tracking_geo import haversine



# ==================================================
# APP INIT
# ==================================================

app = FastAPI(title="HRMS Backend")

# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# ROUTER REGISTRATION
# ==================================================

app.include_router(
    auth_router,
    tags=["Auth"]
)

app.include_router(
    admin_router,
    tags=["Admin"]
)

app.include_router(
    employee_router,
    tags=["Employee"]
)

app.include_router(
    candidate_router,
    prefix="/candidates",
    tags=["Candidate Evaluation"]
)

# ==================================================
# EMPLOYEE CREATE (LEGACY)
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
# EMPLOYEE PROFILE
# ==================================================

@app.get("/employee/{emp_code}")
def get_profile(emp_code: str):
    profile = employee_profile_edit.get_employee_profile(emp_code)
    if not profile.get("employee"):
        raise HTTPException(status_code=404, detail="Employee not found")
    return profile


@app.put("/employee/{emp_code}/personal")
def update_personal(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_personal(emp_code, data)


@app.put("/employee/{emp_code}/official")
def update_official(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_official(emp_code, data)


@app.put("/employee/{emp_code}/family")
def update_family(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_family(emp_code, data)


@app.put("/employee/{emp_code}/vehicle")
def update_vehicle(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.update_vehicle(emp_code, data)


@app.put("/employee/{emp_code}/statutory")
def update_statutory(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.upsert_statutory(emp_code, data)


@app.put("/employee/{emp_code}/emergency-contacts")
def update_contacts(emp_code: str, data: dict = Body(...)):
    return employee_profile_edit.upsert_emergency_contacts(
        emp_code,
        data.get("contacts", [])
    )

# ==================================================
# LEAVE APPROVAL
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
# DASHBOARD SUMMARY
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
        

#=================================================================
#employee Tracking
#=================================================================

# =================================================
# APP SETUP
# =================================================

app = FastAPI(title="HRMS Live Tracking")
manager = ConnectionManager()


# =================================================
# RUNTIME MEMORY
# =================================================

employees = {}

IDLE_TIME = 600        # 10 minutes
OFFLINE_TIME = 1800    # 30 minutes


# =================================================
# LOGIN
# =================================================

@app.post("/api/login")
async def login(
    employeeId: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    row = db.execute(
        text("""
            SELECT emp_code, first_name
            FROM employees
            WHERE emp_code = :e AND password = :p
        """),
        {"e": employeeId, "p": password}
    ).fetchone()

    if not row:
        return {"ok": False}

    employees[employeeId] = {
        "name": row.first_name,
        "last_seen": time.time(),
        "status": "Active",
        "current_site": None,
        "lat": None,
        "lng": None,
        "geofences": {}
    }

    await manager.broadcast({
        "type": "employee_online",
        "employeeId": employeeId
    })

    return {"ok": True}

@app.post("/api/admin/geofence")
def create_geofence(
    name: str = Form(...),
    center_lat: float = Form(...),
    center_lng: float = Form(...),
    radius_meters: float = Form(...),
    db: Session = Depends(get_db)
):
    db.execute(
        text("""
            INSERT INTO geofences
            (name, center_lat, center_lng, radius_meters)
            VALUES (:n, :lat, :lng, :r)
        """),
        {
            "n": name,
            "lat": center_lat,
            "lng": center_lng,
            "r": radius_meters
        }
    )

    db.commit()

    return {
        "ok": True,
        "message": "Geofence added successfully"
    }


# =================================================
# LOCATION UPDATE
# =================================================

@app.post("/api/location")
async def update_location(
    employeeId: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    db: Session = Depends(get_db)
):
    now = time.time()

    if employeeId not in employees:
        employees[employeeId] = {
            "name": employeeId,
            "geofences": {}
        }

    emp = employees[employeeId]
    emp["last_seen"] = now
    emp["lat"] = lat
    emp["lng"] = lng

    geofences = db.execute(
        text("SELECT * FROM geofences WHERE is_active = true")
    ).fetchall()

    status = "Moving"
    site = None

    for g in geofences:
        distance = haversine(lat, lng, g.center_lat, g.center_lng)

        current = "INSIDE" if distance <= g.radius_meters else "OUTSIDE"
        previous = emp["geofences"].get(g.id)

        if current == "INSIDE":
            status = "On-site"
            site = g.name

        # ENTER / EXIT EVENT
        if previous and previous != current:
            event = "ENTER" if current == "INSIDE" else "EXIT"

            db.execute(
                text("""
                    INSERT INTO geofence_events
                    (emp_code, geofence_id, event_type, latitude, longitude)
                    VALUES (:e, :g, :ev, :lat, :lng)
                """),
                {
                    "e": employeeId,
                    "g": g.id,
                    "ev": event,
                    "lat": lat,
                    "lng": lng
                }
            )

            await manager.broadcast({
                "type": "geofence_event",
                "employeeId": employeeId,
                "site": g.name,
                "event": event
            })

        emp["geofences"][g.id] = current

    emp["status"] = status
    emp["current_site"] = site

    # SAVE LOCATION HISTORY
    db.execute(
        text("""
            INSERT INTO employee_locations
            (emp_code, latitude, longitude, geofence_id, geofence_status)
            VALUES (:e, :lat, :lng, :gid, :gs)
        """),
        {
            "e": employeeId,
            "lat": lat,
            "lng": lng,
            "gid": None,
            "gs": status
        }
    )

    db.commit()
    return {"ok": True}


# =================================================
# ADMIN — LIVE EMPLOYEES
# =================================================

@app.get("/api/admin/live-employees")
def live_employees(
    search: Optional[str] = Query(None),
    site: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    now = time.time()
    result = []

    for emp_id, emp in employees.items():

        diff = now - emp["last_seen"]

        if diff > OFFLINE_TIME:
            current_status = "Offline"
        elif diff > IDLE_TIME:
            current_status = "Idle"
        else:
            current_status = emp.get("status", "Moving")

        emp_name = emp.get("name", emp_id)

        if search and search.lower() not in emp_name.lower():
            continue
        if site and emp.get("current_site") != site:
            continue
        if status and current_status != status:
            continue

        result.append({
            "employeeId": emp_id,
            "employeeName": emp_name,
            "current_site": emp.get("current_site"),
            "status": current_status,
            "last_ping": f"{int(diff / 60)} min ago"
        })

    return result


# =================================================
# ADMIN — ACTIVE SITES
# =================================================

@app.get("/api/admin/active-sites")
def active_sites(db: Session = Depends(get_db)):
    counter = Counter()

    for emp in employees.values():
        if emp.get("status") == "On-site" and emp.get("current_site"):
            counter[emp["current_site"]] += 1

    total_sites = db.execute(
        text("SELECT COUNT(*) FROM geofences WHERE is_active = true")
    ).scalar()

    return {
        "total_sites": total_sites,
        "active_sites": len(counter),
        "sites": [
            {"site": site, "employees": count}
            for site, count in counter.items()
        ]
    }


# =================================================
# ADMIN — EMPLOYEE LOCATION HISTORY
# =================================================

@app.get("/api/admin/employee/{emp_code}/history")
def employee_location_history(
    emp_code: str,
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
            SELECT latitude, longitude, timestamp
            FROM employee_locations
            WHERE emp_code = :e
            ORDER BY timestamp DESC
            LIMIT 500
        """),
        {"e": emp_code}
    ).fetchall()

    return {
        "employeeId": emp_code,
        "history": [
            {
                "lat": r.latitude,
                "lng": r.longitude,
                "time": r.timestamp.isoformat()
            }
            for r in rows
        ]
    }


# =================================================
# ADMIN — GEOFENCE EVENT HISTORY
# =================================================

@app.get("/api/admin/employee/{emp_code}/geofence-events")
def employee_geofence_events(
    emp_code: str,
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
            SELECT g.name, e.event_type, e.ts
            FROM geofence_events e
            JOIN geofences g ON g.id = e.geofence_id
            WHERE e.emp_code = :e
            ORDER BY e.ts DESC
        """),
        {"e": emp_code}
    ).fetchall()

    return [
        {
            "site": r.name,
            "event": r.event_type,
            "time": r.ts.isoformat()
        }
        for r in rows
    ]


# ================================================
#   FIELD REPORT
# ================================================

@app.post("/api/employee/field-report")
def submit_field_report(
    emp_code: str = Form(...),
    report_date: str = Form(...),
    client_name: str = Form(...),
    activities: str = Form(...),
    remarks: str = Form(None),
    latitude: float = Form(...),
    longitude: float = Form(...),
    location_address: str = Form(None),
    db: Session = Depends(get_db)
):
    # detect geofence
    geofences = db.execute(
        text("SELECT * FROM geofences WHERE is_active=true")
    ).fetchall()

    geofence_id = None
    geofence_status = "OUTSIDE"

    for g in geofences:
        distance = haversine(
            latitude,
            longitude,
            g.center_lat,
            g.center_lng
        )
        if distance <= g.radius_meters:
            geofence_id = g.id
            geofence_status = "INSIDE"
            break

    db.execute(
        text("""
            INSERT INTO field_work_reports (
                emp_code,
                report_date,
                client_name,
                activities,
                remarks,
                latitude,
                longitude,
                location_address,
                geofence_id,
                geofence_status
            )
            VALUES (
                :e, :d, :c, :a, :r,
                :lat, :lng, :addr,
                :gid, :gs
            )
        """),
        {
            "e": emp_code,
            "d": report_date,
            "c": client_name,
            "a": activities,
            "r": remarks,
            "lat": latitude,
            "lng": longitude,
            "addr": location_address,
            "gid": geofence_id,
            "gs": geofence_status
        }
    )

    db.commit()

    return {
        "ok": True,
        "message": "Field work report submitted"
    }

# ================================================
#   EMPLOYEE — MY REPORT HISTORY
# ================================================

@app.get("/api/employee/field-report/history/{emp_code}")
def employee_report_history(
    emp_code: str,
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
            SELECT
                report_date,
                client_name,
                activities,
                location_address,
                created_at
            FROM field_work_reports
            WHERE emp_code = :e
            ORDER BY report_date DESC
        """),
        {"e": emp_code}
    ).fetchall()

    return [
        {
            "date": r.report_date,
            "client": r.client_name,
            "activities": r.activities,
            "location": r.location_address,
            "submitted_at": r.created_at.isoformat()
        }
        for r in rows
    ]


# ===============================================
#  ADMIN — ALL FIELD REPORTS
# ================================================

@app.get("/api/admin/field-reports")
def admin_all_reports(db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT
                emp_code,
                report_date,
                client_name,
                activities,
                location_address,
                geofence_status,
                created_at
            FROM field_work_reports
            ORDER BY created_at DESC
        """)
    ).fetchall()

    return [
        {
            "employee": r.emp_code,
            "date": r.report_date,
            "client": r.client_name,
            "activities": r.activities,
            "location": r.location_address,
            "geofence": r.geofence_status,
            "time": r.created_at.isoformat()
        }
        for r in rows
    ]


# =================================================
# ADMIN WEBSOCKET
# =================================================

@app.websocket("/ws/admin")
async def admin_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
