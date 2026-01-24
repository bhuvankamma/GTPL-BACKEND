from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from database_holiday import get_db
from crud import holiday_cal_crud
from schemas.schemas_holiday import (
    WeeklyOffBulkUpdate,
    HolidayCreate,
    HolidayUpdate,
    WeeklyOffUpdate
)

from models.holiday_cal_sravya import Holiday

router = APIRouter(prefix="/holidays", tags=["Holidays"])


def generate_ics(holidays):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HRMS//Holiday Calendar//EN"
    ]

    for h in holidays:
        lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{h.title}",
            f"DTSTART;VALUE=DATE:{h.date.strftime('%Y%m%d')}",
            f"DESCRIPTION:{h.description or ''}",
        ])

        if h.recurring == "yearly":
            lines.append("RRULE:FREQ=YEARLY")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\n".join(lines)


@router.post("/")
def add_holiday(data: HolidayCreate, db: Session = Depends(get_db)):
    return holiday_cal_crud.create_holiday(db, data)


@router.put("/{holiday_id}")
def edit_holiday(holiday_id: int, data: HolidayUpdate, db: Session = Depends(get_db)):
    return holiday_cal_crud.update_holiday(db, holiday_id, data)


@router.delete("/{holiday_id}")
def delete_holiday(holiday_id: int, db: Session = Depends(get_db)):
    return holiday_cal_crud.delete_holiday(db, holiday_id)


@router.get("/")
def list_holidays(db: Session = Depends(get_db)):
    return holiday_cal_crud.get_all_holidays(db)


@router.get("/upcoming")
def upcoming_holidays(db: Session = Depends(get_db)):
    return holiday_cal_crud.get_upcoming_holidays(db)


@router.get("/{holiday_id}/ics")
def single_holiday_ics(holiday_id: int, db: Session = Depends(get_db)):
    holiday = db.query(Holiday).filter(
        Holiday.id == holiday_id,
        Holiday.is_active == True
    ).first()

    ics_content = generate_ics([holiday])
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={holiday.title}.ics"
        }
    )


@router.get("/ics")
def export_all_ics(db: Session = Depends(get_db)):
    holidays = holiday_cal_crud.get_all_holidays(db)
    ics_content = generate_ics(holidays)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=company_holidays.ics"
        }
    )
