from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form
)
from database_policy import get_db_conn
from utils.auth_policy import get_current_user
from utils.s3_utils_policy import upload_policy_pdf
from schemas.schemas_policy import AcknowledgePolicy

router = APIRouter(tags=["Policies"])


# =========================================================
# 1️⃣ ADMIN – CREATE POLICY
# =========================================================
@router.post("/policies", summary="Create Policy (Admin only)")
def create_policy(
    title: str = Form(...),
    version: str = Form(...),
    is_general: bool = Form(...),
    applicable_roles: str = Form(""),
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    if user["role"] != "ADMIN":
        raise HTTPException(403, "Only Admin can create policies")

    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files allowed")

    # ✅ DEFINE IT FIRST (THIS WAS MISSING)
    applies_to = "all" if is_general else "specific"

    conn = get_db_conn()
    cur = conn.cursor()

    # ✅ get next sequence value
    cur.execute("SELECT nextval('policies_id_seq')")
    next_id = cur.fetchone()[0]

    policy_code = f"POL-{next_id:03d}"

    # ✅ INSERT WITH policy_id
    cur.execute("""
        INSERT INTO policies
        (id, policy_id, title, version, applies_to, status, deleted, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, 'PUBLISHED', false, now(), now())
    """, (
        next_id,
        policy_code,
        title,
        version,
        applies_to
    ))

    # ✅ Upload PDF
    s3_key = upload_policy_pdf(
        file_obj=file.file,
        filename=file.filename,
        policy_id=policy_code,
        version=version
    )

    # ✅ Update document path
    cur.execute("""
        UPDATE policies
        SET document_path = %s
        WHERE id = %s
    """, (s3_key, next_id))

    # ✅ Role mapping
    if not is_general and applicable_roles:
        for role in [r.strip() for r in applicable_roles.split(",")]:
            cur.execute("""
                INSERT INTO policy_roles (policy_id, role)
                VALUES (%s, %s)
            """, (next_id, role))

    conn.commit()
    cur.close()

    return {
        "message": "Policy created successfully",
        "policy_id": policy_code
    }
###################################
# 1️⃣ ADMIN – EDIT POLICY
####################################
@router.put("/policies/{policy_id}", summary="Edit Policy (Admin only)")
def edit_policy(
    policy_id: int,
    title: str = Form(...),
    version: str = Form(...),
    is_general: bool = Form(...),
    applicable_roles: str = Form(""),
    file: UploadFile | None = File(None),
    user=Depends(get_current_user)
):
    if user["role"] != "ADMIN":
        raise HTTPException(403, "Admin only")

    conn = get_db_conn()
    cur = conn.cursor()

    # 🚫 Block edit if acknowledged
    cur.execute("""
        SELECT 1
        FROM policy_employee_map
        WHERE policy_id = %s AND acknowledged = true
        LIMIT 1
    """, (policy_id,))

    if cur.fetchone():
        raise HTTPException(
            400,
            "Policy already acknowledged. Editing not allowed."
        )

    applies_to = "all" if is_general else "specific"

    cur.execute("""
        UPDATE policies
        SET title = %s,
            version = %s,
            applies_to = %s,
            updated_at = now()
        WHERE id = %s AND deleted = false
    """, (title, version, applies_to, policy_id))

    # Optional PDF update
    if file:
        from app.s3_utils import upload_policy_pdf
        s3_key = upload_policy_pdf(
            file_obj=file.file,
            filename=file.filename,
            policy_id=f"POL-{policy_id:03d}",
            version=version
        )
        cur.execute("""
            UPDATE policies
            SET document_path = %s
            WHERE id = %s
        """, (s3_key, policy_id))

    # Update roles
    cur.execute("DELETE FROM policy_roles WHERE policy_id = %s", (policy_id,))
    if not is_general and applicable_roles:
        for role in applicable_roles.split(","):
            cur.execute("""
                INSERT INTO policy_roles (policy_id, role)
                VALUES (%s, %s)
            """, (policy_id, role.strip()))

    conn.commit()
    cur.close()

    return {"message": "Policy updated successfully"}
# =========================================================
# 3 ADMIN - DELETE POLICY
# =========================================================
@router.delete("/policies/{policy_id}", summary="Delete Policy (Admin only)")
def delete_policy(policy_id: int, user=Depends(get_current_user)):
    if user["role"] != "ADMIN":
        raise HTTPException(403, "Admin only")

    conn = get_db_conn()
    cur = conn.cursor()

    # 🚫 Prevent delete if acknowledged
    cur.execute("""
        SELECT 1
        FROM policy_employee_map
        WHERE policy_id = %s AND acknowledged = true
        LIMIT 1
    """, (policy_id,))

    if cur.fetchone():
        raise HTTPException(
            400,
            "Policy already acknowledged. Deletion not allowed."
        )

    cur.execute("""
        UPDATE policies
        SET deleted = true,
            status = 'DELETED',
            updated_at = now()
        WHERE id = %s
    """, (policy_id,))

    conn.commit()
    cur.close()

    return {"message": "Policy deleted successfully"}


# =========================================================
# 2️⃣ VIEW POLICIES (ROLE BASED)
# =========================================================
@router.get("/policies", summary="View Policies (Role based)")
def view_policies(user=Depends(get_current_user)):
    conn = get_db_conn()
    cur = conn.cursor()

    if user["role"] == "ADMIN":
        cur.execute("SELECT * FROM policies WHERE deleted = false")

    elif user["role"] == "MANAGER":
        cur.execute("""
            SELECT * FROM policies
            WHERE deleted = false
            AND (applies_to = 'all'
                 OR id IN (SELECT policy_id FROM policy_roles WHERE role = 'MANAGER'))
        """)

    else:  # EMPLOYEE
        cur.execute("""
            SELECT * FROM policies
            WHERE deleted = false
            AND (applies_to = 'all'
                 OR id IN (SELECT policy_id FROM policy_roles WHERE role = 'EMPLOYEE'))
        """)

    rows = cur.fetchall()
    cur.close()
    return rows


# =========================================================
# 3️⃣ EMPLOYEE – ACKNOWLEDGE POLICY (FINAL & CORRECT)
# =========================================================
@router.post("/policies/acknowledge", summary="Acknowledge Policy")
def acknowledge_policy(
    data: AcknowledgePolicy,
    user=Depends(get_current_user)
):
    if user["role"] != "EMPLOYEE":
        raise HTTPException(403, "Only employees can acknowledge")

    conn = get_db_conn()
    cur = conn.cursor()

    # 1️⃣ Update assignment table
    cur.execute("""
        UPDATE policy_employee_map
        SET acknowledged = true,
            acknowledged_at = now()
        WHERE policy_id = %s
          AND employee_id = %s
    """, (data.policy_id, user["emp_id"]))

    if cur.rowcount == 0:
        raise HTTPException(
            400,
            "Policy not assigned to this employee"
        )

    conn.commit()
    cur.close()

    return {"message": "Policy acknowledged successfully"}


# =========================================================
# 4️⃣ MANAGER – ACK STATUS (VIEW ONLY) ✅ FINAL
# =========================================================
@router.get("/manager/ack-status", summary="Manager Acknowledgement Status")
def manager_ack_status(user=Depends(get_current_user)):
    if user["role"] != "MANAGER":
        raise HTTPException(403, "Manager only")

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.policy_id,              -- POL-001 (display)
            p.title,
            pem.employee_id,
            CASE
                WHEN pem.acknowledged = true THEN 'ACKNOWLEDGED'
                ELSE 'PENDING'
            END AS status,
            pem.acknowledged_at
        FROM policy_employee_map pem
        JOIN policies p
            ON p.id = pem.policy_id
        ORDER BY p.id, pem.employee_id;
    """)

    rows = cur.fetchall()
    cur.close()

    return rows

@router.get("/dashboard/policy-stats", summary="Policy Dashboard Stats")
def policy_dashboard_stats(user=Depends(get_current_user)):
    if user["role"] not in ["ADMIN", "MANAGER"]:
        raise HTTPException(403, "Not authorized")

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE acknowledged = true) AS completed,
            COUNT(*) FILTER (WHERE acknowledged = false) AS pending
        FROM policy_employee_map
    """)

    total, completed, pending = cur.fetchone()
    cur.close()

    return {
        "total": total,
        "completed": completed,
        "pending": pending
    }


   # =========================================================
# 🔍 DEBUG – CHECK TABLE COLUMNS
# =========================================================
    @router.get("/debug/columns/{table_name}", summary="Debug DB table columns")
    def debug_table_columns(table_name: str):
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))

        columns = cur.fetchall()
        cur.close()

        return [
            {"column_name": col[0], "data_type": col[1]}
            for col in columns
        ]


    rows = cur.fetchall()
    cur.close()
    return rows
