from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.Biomertic_Attandance_biometric import BiometricDevice
from schemas.Biomertic_Attandance_biometric import DeviceCreate, DeviceResponse

router = APIRouter(prefix="/biometric-devices", tags=["Biometric Devices"])


# ➕ Add Device
@router.post("/", response_model=DeviceResponse)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    device = BiometricDevice(**payload.dict())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


# 📄 List Devices
@router.get("/", response_model=list[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    return db.query(BiometricDevice).order_by(BiometricDevice.id.desc()).all()


# ✏️ Edit Device
@router.put("/{device_id}")
def update_device(device_id: int, payload: DeviceCreate, db: Session = Depends(get_db)):
    device = db.query(BiometricDevice).filter(BiometricDevice.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for key, value in payload.dict().items():
        setattr(device, key, value)

    db.commit()
    return {"message": "Device updated successfully"}


# 🗑️ Delete Device
@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(BiometricDevice).filter(BiometricDevice.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return {"message": "Device deleted successfully"}
