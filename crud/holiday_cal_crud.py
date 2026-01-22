from sqlalchemy.orm import Session
from models.holiday_cal_sravya import Holiday, WeeklyOff
from datetime import date



# -------- HOLIDAYS --------
def create_holiday(db: Session, data):
    holiday = Holiday(**data.dict())
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday

def update_holiday(db, holiday_id, data):
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()

    for key, value in data.dict().items():
        setattr(holiday, key, value)

    db.commit()
    db.refresh(holiday)   # 🔑 get updated data
    return holiday        # 🔑 RETURN IT


def delete_holiday(db, holiday_id):
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()

    holiday.is_active = False
    db.commit()

    return {
        "status": "success",
        "message": "Holiday deleted successfully"
    }


def get_all_holidays(db: Session):
    return db.query(Holiday).filter(Holiday.is_active == True).all()


def get_upcoming_holidays(db: Session, limit=5):
    return (
        db.query(Holiday)
        .filter(Holiday.date >= date.today(), Holiday.is_active == True)
        .order_by(Holiday.date)
        .limit(limit)
        .all()
    )


# -------- WEEKLY OFFS --------
def set_weekly_off(db, day, is_off):
    # Normalize day format: Sun, Mon, Tue...
    normalized_day = day.strip().capitalize()

    weekly = db.query(WeeklyOff).filter(
        WeeklyOff.day == normalized_day
    ).first()

    if weekly:
        weekly.is_off = is_off
    else:
        weekly = WeeklyOff(day=normalized_day, is_off=is_off)
        db.add(weekly)

    db.commit()

def set_bulk_weekly_off(db, off_days):
    normalized = [d.strip().capitalize() for d in off_days]
    all_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    for day in all_days:
        weekly = db.query(WeeklyOff).filter(WeeklyOff.day == day).first()
        if weekly:
            weekly.is_off = day in normalized
        else:
            weekly = WeeklyOff(day=day, is_off=day in normalized)
            db.add(weekly)

    db.commit()


def get_weekly_offs(db: Session):
    return db.query(WeeklyOff).all()
