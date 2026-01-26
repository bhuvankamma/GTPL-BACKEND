from sqlalchemy.orm import Session
from models.models_generalsettings import Settings
from schemas.schemas_generalsettings import SettingsCreate


def get_settings(db: Session):
    return db.query(Settings).first()

def create_or_update_settings(db: Session, payload: SettingsCreate):
    instance = db.query(Settings).first()

    if instance:
        instance.system_name = payload.system_name
        instance.timezone = payload.timezone
        instance.date_format = payload.date_format
    else:
        instance = Settings(
            system_name=payload.system_name,
            timezone=payload.timezone,
            date_format=payload.date_format,
        )
        db.add(instance)

    db.commit()
    db.refresh(instance)
    return instance
