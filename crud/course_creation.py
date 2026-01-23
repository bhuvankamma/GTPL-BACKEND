from sqlalchemy.orm import Session
from sqlalchemy import func, text

from utils.course_creation import link_status
from models.course_creation import Portal, Module, Lesson


# =====================================================
# PORTAL CRUD
# =====================================================

def list_portals(db: Session):
    return db.query(Portal).filter(
        Portal.is_deleted == False
    ).order_by(Portal.created_at.desc()).all()


def get_portal(db: Session, portal_id: int):
    return db.query(Portal).filter(
        Portal.id == portal_id,
        Portal.is_deleted == False
    ).first()


def create_portal(db: Session, data):
    portal = Portal(
        title=data.title,
        category=data.category,
        description=data.description,
        status=data.status,
        deadline_date=data.deadline_date,
        is_deleted=False
    )
    db.add(portal)
    db.commit()
    db.refresh(portal)
    return portal


def update_portal(db, portal_id: int, data):
    portal = db.query(Portal).filter(
        Portal.id == portal_id,
        Portal.is_deleted == False
    ).first()

    if not portal:
        return None

    if data.title is not None:
        portal.title = data.title
    if data.description is not None:
        portal.description = data.description
    if data.category is not None:
        portal.category = data.category
    if data.deadline_date is not None:
        portal.deadline_date = data.deadline_date

    db.commit()
    return portal


def update_portal_status(db: Session, portal_id: int, status: str):
    portal = get_portal(db, portal_id)

    if not portal:
        return False

    portal.status = status
    db.commit()
    return True


def soft_delete_portal(db: Session, portal_id: int):
    portal = get_portal(db, portal_id)

    if not portal:
        return False

    portal.is_deleted = True
    db.commit()
    return True


# =====================================================
# MODULE CRUD
# =====================================================

def create_module(
    db: Session,
    portal_id: int,
    title: str,
    module_goal: str
):
    module = Module(
        portal_id=portal_id,
        title=title,
        module_goal=module_goal,
        is_deleted=False
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def get_modules(db: Session, portal_id: int):
    return db.query(Module).filter(
        Module.portal_id == portal_id,
        Module.is_deleted == False
    ).order_by(Module.created_at).all()

def update_module(db: Session, module_id: int, data):
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.is_deleted == False
    ).first()

    if not module:
        return None

    module.title = data.title
    module.module_goal = data.module_goal

    db.commit()
    return module

def soft_delete_module(db: Session, module_id: int):
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.is_deleted == False
    ).first()

    if not module:
        return False

    module.is_deleted = True
    db.commit()
    return True


# =====================================================
# LESSON CRUD
# =====================================================

def create_lesson(db: Session, data):
    status = link_status(data.content_url)

    lesson = Lesson(
        module_id=data.module_id,
        title=data.title,
        content_type=data.content_type,
        content_url=data.content_url,
        content_link_status=status,
        is_deleted=False
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def update_lesson(db: Session, lesson_id: int, data):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.is_deleted == False
    ).first()

    if not lesson:
        return None

    lesson.title = data.title
    lesson.content_type = data.content_type
    lesson.content_url = data.content_url
    lesson.content_link_status = link_status(data.content_url)

    db.commit()
    return lesson



def soft_delete_lesson(db: Session, lesson_id: int):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.is_deleted == False
    ).first()

    if not lesson:
        return False

    lesson.is_deleted = True
    db.commit()
    return True


def get_lessons(db: Session, module_id: int):
    return db.query(Lesson).filter(
        Lesson.module_id == module_id,
        Lesson.is_deleted == False
    ).order_by(Lesson.created_at).all()

def calculate_course_progress(db, portal_id: int, emp_code: str) -> int:
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

    completed = db.execute(
        text("""
            SELECT COUNT(*)
            FROM lesson_progress lp
            JOIN lessons l ON lp.lesson_id = l.id
            JOIN modules m ON l.module_id = m.id
            WHERE m.portal_id = :portal_id
              AND lp.emp_code = :emp_code
        """),
        {
            "portal_id": portal_id,
            "emp_code": emp_code
        }
    ).scalar()

    return int((completed / total) * 100)
