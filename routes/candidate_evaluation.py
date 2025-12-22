import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from main import get_cursor
from schemas.candidate_evaluation import CandidateCreate, CandidateUpdate

router = APIRouter()

UPLOAD_DIR = "uploads/reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------- CREATE ----------------
@router.post("/")
def create_candidate_api(data: CandidateCreate):
    conn, cur = get_cursor()
    try:
        status = "Selected" if data.technical_skill and data.communication_skill else "Rejected"

        cur.execute("""
            INSERT INTO candidates
            (
                full_name,
                email,
                mobile,
                position,
                technical_skill,
                communication_skill,
                technical_feedback,
                communication_feedback,
                overall_feedback,
                status
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            data.full_name,
            data.email,
            data.mobile,
            data.position,
            data.technical_skill,
            data.communication_skill,
            data.technical_feedback,
            data.communication_feedback,
            data.overall_feedback,
            status
        ))

        candidate_id = cur.fetchone()[0]
        conn.commit()

        return {"id": candidate_id, "status": status}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


# ---------------- UPLOAD DOCUMENT ----------------
@router.post("/{candidate_id}/upload")
def upload_report(candidate_id: int, file: UploadFile = File(...)):
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT id FROM candidates WHERE id=%s", (candidate_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Candidate not found")

        file_path = f"{UPLOAD_DIR}/{candidate_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        cur.execute(
            "UPDATE candidates SET report_file=%s WHERE id=%s",
            (file_path, candidate_id)
        )
        conn.commit()

        return {"message": "File uploaded", "path": file_path}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


# ---------------- GET ALL ----------------
@router.get("/")
def get_all_candidates():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT * FROM candidates ORDER BY id DESC")
        rows = cur.fetchall()

        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]

    finally:
        cur.close()
        conn.close()


# ---------------- GET BY ID ----------------
@router.get("/{candidate_id}")
def get_candidate(candidate_id: int):
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT * FROM candidates WHERE id=%s", (candidate_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Candidate not found")

        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))

    finally:
        cur.close()
        conn.close()


# ---------------- UPDATE ----------------
@router.put("/{candidate_id}")
def update_candidate_api(candidate_id: int, data: CandidateUpdate):
    conn, cur = get_cursor()
    try:
        fields = []
        values = []

        for key, value in data.dict(exclude_unset=True).items():
            fields.append(f"{key}=%s")
            values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        values.append(candidate_id)

        cur.execute(
            f"UPDATE candidates SET {', '.join(fields)} WHERE id=%s",
            tuple(values)
        )

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Candidate not found")

        conn.commit()
        return {"status": "updated"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


# ---------------- DELETE ----------------
@router.delete("/{candidate_id}")
def delete_candidate_api(candidate_id: int):
    conn, cur = get_cursor()
    try:
        cur.execute("DELETE FROM candidates WHERE id=%s", (candidate_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Candidate not found")

        conn.commit()
        return {"message": "Candidate deleted"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()
