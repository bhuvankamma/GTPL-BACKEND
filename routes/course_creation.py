from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import text
from database_B import SessionLocal
from crud import course_creation
from models.course_creation import Lesson
from database import SessionLocal
from crud import course_creation
from models.course_creation import Portal
from schemas.course_creation import (
    PortalCreate,
    PortalUpdate,
    PortalStatusUpdate,
    ModuleCreate,
    LessonCreate,
    LessonComplete     
)
from utils.course_creation import manager_only

# =====================================================
# DB DEPENDENCY
# =====================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()


# =====================================================
# PORTAL ROUTES
# =====================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()


# =====================================================
# PORTAL ROUTES
# =====================================================
# 1️⃣ LIST PORTALS
@router.get("/portal")
def list_portals(db: Session = Depends(get_db)):
    return course_creation.list_portals(db)


# 2️⃣ CREATE PORTAL (Manager only)
@router.post("/portal", dependencies=[Depends(manager_only)])
def create_portal(
    data: PortalCreate,
    db: Session = Depends(get_db)
):
    portal = course_creation.create_portal(db, data)
    return {"portal_id": portal.id}

'''
# 3️⃣ GET SINGLE PORTAL
@router.get("/portal/{portal_id}")
def get_portal(portal_id: int, db: Session = Depends(get_db)):
    portal = crud.get_portal(db, portal_id)
    if not portal:
        raise HTTPException(status_code=404, detail="Portal not found")
    return portal


# 4️⃣ UPDATE PORTAL (Manager only)
@router.put("/portal/{portal_id}", dependencies=[Depends(manager_only)])
def update_portal(
    portal_id: int,
    data: PortalUpdate,
    db: Session = Depends(get_db)
):
    portal = crud.update_portal(db, portal_id, data)
    if not portal:
        raise HTTPException(status_code=404, detail="Portal not found")
    return {"message": "Portal updated"}

'''

# 5️⃣ UPDATE PORTAL STATUS (Manager only)
@router.put("/portal/status", dependencies=[Depends(manager_only)])
def update_portal_status(
    data: PortalStatusUpdate,
    db: Session = Depends(get_db)
):
    success = course_creation.update_portal_status(db, data.portal_id, data.status)
    if not success:
        raise HTTPException(status_code=404, detail="Portal not found")
    return {"message": f"Portal status updated to {data.status}"}

'''
# 6️⃣ DELETE PORTAL (Soft delete)
@router.put("/portal/delete", dependencies=[Depends(manager_only)])
def delete_portal(
    portal_id: int,
    db: Session = Depends(get_db)
):
    success = crud.soft_delete_portal(db, portal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Portal not found")
    return {"message": "Portal removed"}
'''
# =====================================================
# MODULE ROUTES
# =====================================================

@router.post("/module", dependencies=[Depends(manager_only)])
def create_module(
    data: ModuleCreate,
    db: Session = Depends(get_db)
):
    module = course_creation.create_module(
        db,
        portal_id=data.portal_id,
        title=data.title,
        module_goal=data.module_goal
    )
    return {"module_id": module.id}


@router.get("/module")
def get_modules(
    portal_id: int,
    db: Session = Depends(get_db)
):
    return course_creation.get_modules(db, portal_id)

@router.put("/module/{module_id}", dependencies=[Depends(manager_only)])
def update_module(
    module_id: int,
    data: ModuleCreate,
    db: Session = Depends(get_db)
):
    module = course_creation.update_module(db, module_id, data)

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"message": "Module updated"}


@router.put("/module/delete")
def delete_module(
    module_id: int,
    db: Session = Depends(get_db)
):
    success = course_creation.soft_delete_module(db, module_id)

    if not success:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"message": "Module and its lessons removed from frontend"}

# =====================================================
# LESSON ROUTES
# =====================================================

@router.post("/lesson", dependencies=[Depends(manager_only)])
def create_lesson(
    data: LessonCreate,
    db: Session = Depends(get_db)
):
    lesson = course_creation.create_lesson(db, data)
    return {"lesson_id": lesson.id}


@router.get("/lesson")
def get_lessons(
    module_id: int,
    db: Session = Depends(get_db)
):
    return course_creation.get_lessons(db, module_id)

def create_lesson(db: Session, data):
    lesson = Lesson(
        module_id=data.module_id,
        title=data.title,
        content_type=data.content_type,
        content_url=data.content_url,
        content_link_status="Available" if data.content_url else "Missing",
        is_deleted=False
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson

@router.post("/lesson/complete")
def complete_lesson(
    lesson_id: int,
    emp_code: str = Header(..., alias="X-Emp-Code"),
    db: Session = Depends(get_db)
):
    db.execute(
        text("""
            INSERT INTO lesson_progress (emp_code, lesson_id, status)
            VALUES (:emp_code, :lesson_id, 'completed')
            ON CONFLICT (emp_code, lesson_id)
            DO NOTHING
        """),
        {
            "emp_code": emp_code,
            "lesson_id": lesson_id
        }
    )
    db.commit()
    return {"message": "Lesson completed"}

@router.put("/lesson/{lesson_id}", dependencies=[Depends(manager_only)])
def update_lesson(
    lesson_id: int,
    data: LessonCreate,
    db: Session = Depends(get_db)
):
    lesson = course_creation.update_lesson(db, lesson_id, data)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"message": "Lesson updated"}


@router.put("/lesson/delete")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    success = course_creation.soft_delete_lesson(db, lesson_id)

    if not success:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"message": "Lesson removed from frontend"}

# =====================================================
# DASHBOARD ROUTES (READ-ONLY)
# =====================================================

# 7️⃣ ACTIVE COURSES (Published)
@router.get("/dashboard/active-courses")
def get_active_courses(db: Session = Depends(get_db)):
    return db.query(Portal).filter(
        Portal.is_deleted == False,
        func.lower(func.trim(Portal.status)) == "published"
    ).all()

def calculate_course_progress(db: Session, portal_id: int, emp_code: str) -> int:
    # total lessons in course
    total = db.execute(
        text("""
            SELECT COUNT(*)
            FROM lessons l
            JOIN modules m ON l.module_id = m.id
            WHERE m.portal_id = :portal_id
              AND l.is_deleted = false
        """),
        {"portal_id": portal_id}
    ).scalar()

    if total == 0:
        return 0

    # completed lessons by employee
    completed = db.execute(
        text("""
            SELECT COUNT(*)
            FROM lesson_progress lp
            JOIN lessons l ON lp.lesson_id = l.id
            JOIN modules m ON l.module_id = m.id
            WHERE m.portal_id = :portal_id
              AND lp.emp_code = :emp_code
              AND lp.status = 'completed'
        """),
        {
            "portal_id": portal_id,
            "emp_code": emp_code
        }
    ).scalar()

    return int((completed / total) * 100)

# 8️⃣ COURSE STATUS (PIE CHART)
@router.get("/dashboard/course-progress")
def get_course_progress(db: Session = Depends(get_db)):
    # base courses (not deleted)
    courses = db.query(Portal).filter(
        (Portal.is_deleted == False) | (Portal.is_deleted.is_(None))
    ).all()

    assigned = in_progress = completed = 0

    for course in courses:
        module_count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM modules
                WHERE portal_id = :portal_id
                  AND is_deleted = false
            """),
            {"portal_id": course.id}
        ).scalar()

        status = (course.status or "").strip().lower()

        if status == "published":
            completed += 1
        elif module_count > 0:
            in_progress += 1
        else:
            assigned += 1

    return {
        "assigned": assigned,
        "in_progress": in_progress,
        "completed": completed,
        "total": assigned + in_progress + completed
    }


@router.get("/dashboard/upcoming-deadlines")
def get_upcoming_deadlines(db: Session = Depends(get_db)):
    courses = db.query(Portal).filter(
        Portal.is_deleted == False,
        Portal.deadline_date.isnot(None)
    ).order_by(Portal.deadline_date.asc()).limit(5).all()

    return [
        {
            "portal_id": c.id,
            "title": c.title,
            "day": c.deadline_date.strftime("%d"),
            "month": c.deadline_date.strftime("%b")
        }
        for c in courses
    ]
'''
@router.get("/my-courses")
def get_my_courses(
  #  emp_code: str = Header(..., alias="X-Emp-Code"),
    db: Session = Depends(get_db)
):
    courses = db.query(Portal).filter(
        Portal.status == "Published",
        Portal.is_deleted == False
    ).all()

    result = []
    for course in courses:
        progress = calculate_course_progress(db, course.id)

        result.append({
            "portal_id": course.id,
            "title": course.title,
            "progress": progress
        })

    return result
'''