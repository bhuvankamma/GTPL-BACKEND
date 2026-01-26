from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from utils.deps_generalsettings import get_db
from crud.general_settings_crud import get_settings, create_or_update_settings
from schemas.schemas_generalsettings import SettingsCreate, SettingsOut

router = APIRouter()
# ---------------- DROPDOWNS ----------------

@router.get("/timezones")
def get_timezones():
    return {
        "timezones": [
            {"label": "India Standard Time (IST)", "value": "IST"},
            {"label": "Eastern Standard Time (EST)", "value": "EST"},
            {"label": "Greenwich Mean Time (GMT)", "value": "GMT"},
        ]
    }

@router.get("/date-formats")
def get_date_formats():
    return {
        "date_formats": [
            "DD/MM/YYYY",
            "MM/DD/YYYY",
            "YYYY-MM-DD",
        ]
    }

# ---------------- SETTINGS ----------------

@router.post("/settings", response_model=SettingsOut)
def create_settings(
    payload: SettingsCreate,
    db: Session = Depends(get_db),
):
    return create_or_update_settings(db, payload)


@router.get("/settings", response_model=Optional[SettingsOut])
def read_settings(db: Session = Depends(get_db)):
    return get_settings(db)
