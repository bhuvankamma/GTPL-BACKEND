import os
from datetime import date
from typing import Optional

import pg8000
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# =================================================
# LOAD ENV VARIABLES
# =================================================
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# =================================================
# FASTAPI APP
# =================================================
app = FastAPI(title="Asset Allocation Backend")

# =================================================
# CORS CONFIG (IMPORTANT)
# =================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://www.wysele.in",
        "https://wysele.in"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================================================
# DB CONNECTION
# =================================================
def get_connection():
    return pg8000.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

# =================================================
# INIT TABLES (RUN ON STARTUP)
# =================================================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            asset_name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS asset_allocations (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
            emp_code VARCHAR(50),
            assigned_date DATE,
            return_date DATE
        )
    """)

    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception as e:
        print("⚠️ DB init skipped:", e)


# =================================================
# REQUEST MODELS
# =================================================
class AssetCreate(BaseModel):
    asset_name: str
    category: str
    status: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_date: Optional[date] = None
    return_date: Optional[date] = None

# =================================================
# ROUTES
# =================================================

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/assets")
def get_assets(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            a.id,
            a.asset_name,
            a.category,
            a.status,
            a.description,
            al.emp_code,
            al.assigned_date,
            al.return_date
        FROM assets a
        LEFT JOIN asset_allocations al ON a.id = al.asset_id
        WHERE 1=1
    """
    values = []

    if category:
        query += " AND a.category = %s"
        values.append(category)

    if search:
        s = f"%{search}%"
        query += " AND (a.asset_name ILIKE %s OR al.emp_code ILIKE %s)"
        values.extend([s, s])

    cur.execute(query, values)
    rows = cur.fetchall()
    conn.close()

    assets = []
    for r in rows:
        assets.append({
            "id": r[0],
            "asset_name": r[1],
            "category": r[2],
            "status": r[3],
            "description": r[4],
            "assigned_to": r[5],
            "assigned_date": r[6].isoformat() if r[6] else None,
            "return_date": r[7].isoformat() if r[7] else None
        })

    return assets

@app.post("/assets", status_code=201)
def add_asset(body: AssetCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO assets (asset_name, category, status, description)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        body.asset_name,
        body.category,
        body.status,
        body.description
    ))

    asset_id = cur.fetchone()[0]

    if body.status == "Assigned":
        if not body.assigned_to or not body.assigned_date:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="assigned_to and assigned_date are required when status is Assigned"
            )

        cur.execute("""
            INSERT INTO asset_allocations
            (asset_id, emp_code, assigned_date, return_date)
            VALUES (%s, %s, %s, %s)
        """, (
            asset_id,
            body.assigned_to,
            body.assigned_date,
            body.return_date
        ))

    conn.commit()
    conn.close()
    return {"message": "Asset added successfully"}

@app.put("/assets/{asset_id}")
def update_asset(asset_id: int, body: AssetCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE assets
        SET asset_name=%s,
            category=%s,
            status=%s,
            description=%s
        WHERE id=%s
    """, (
        body.asset_name,
        body.category,
        body.status,
        body.description,
        asset_id
    ))

    cur.execute("DELETE FROM asset_allocations WHERE asset_id=%s", (asset_id,))

    if body.status == "Assigned":
        cur.execute("""
            INSERT INTO asset_allocations
            (asset_id, emp_code, assigned_date, return_date)
            VALUES (%s, %s, %s, %s)
        """, (
            asset_id,
            body.assigned_to,
            body.assigned_date,
            body.return_date
        ))

    conn.commit()
    conn.close()
    return {"message": "Asset updated successfully"}

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM assets WHERE id=%s", (asset_id,))
    conn.commit()
    conn.close()

    return {"message": "Asset deleted successfully"}

# =================================================
# INCLUDE HR DASHBOARD ROUTES (NEW – SAFE)
# =================================================
from routes.hr_dashboard import router as hr_router
app.include_router(hr_router)
