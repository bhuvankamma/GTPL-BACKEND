from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database_holiday import get_db
from crud import holiday_cal_crud
from schemas.schemas_holiday import(WeeklyOffBulkUpdate,
    HolidayCreate,
    HolidayUpdate,
    WeeklyOffUpdate) 
from models.holiday_cal_sravya import WeeklyOff

router = APIRouter(prefix="/weekly-offs", tags=["Weekly Offs"])


@router.post("/bulk")
def update_bulk_weekly_off(
    data:WeeklyOffBulkUpdate,
    db: Session = Depends(get_db)
):
    holiday_cal_crud.set_bulk_weekly_off(db, data.off_days)
    return {
        "status": "updated",
        "weekly_off": data.off_days
    }


@router.post("/")
def update_weekly_off(
    data:WeeklyOffUpdate,
    db: Session = Depends(get_db)
):
    holiday_cal_crud.set_weekly_off(db, data.day, data.is_off)
    return {"status": "updated"}


@router.get("/")
def get_weekly_offs(db: Session = Depends(get_db)):
    offs = db.query(WeeklyOff).filter(WeeklyOff.is_off == True).all()
    return [o.day for o in offs]
