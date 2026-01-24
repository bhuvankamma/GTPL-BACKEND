from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.Biomertic_Attandance_assignment import DeviceAssignmentRule
from schemas.Biomertic_Attandance_assignment import AssignmentCreate, AssignmentResponse

router = APIRouter(prefix="/device-assignments", tags=["Device Assignments"])


# ➕ Create Assignment
@router.post("/", response_model=AssignmentResponse)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)):
    assignment = DeviceAssignmentRule(**payload.dict())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# 📄 List Assignments
@router.get("/", response_model=list[AssignmentResponse])
def list_assignments(db: Session = Depends(get_db)):
    return db.query(DeviceAssignmentRule).order_by(
        DeviceAssignmentRule.id.desc()
    ).all()


# ✏️ Edit Assignment
@router.put("/{assignment_id}")
def update_assignment(
    assignment_id: int,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(DeviceAssignmentRule)
        .filter(DeviceAssignmentRule.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    for key, value in payload.dict().items():
        setattr(assignment, key, value)

    db.commit()
    return {"message": "Assignment updated successfully"}


# 🗑️ Delete Assignment
@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = (
        db.query(DeviceAssignmentRule)
        .filter(DeviceAssignmentRule.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(assignment)
    db.commit()
    return {"message": "Assignment deleted successfully"}
