from fastapi import APIRouter, HTTPException
from schemas.auth import CreateEmployee
from db import get_db_conn
from crud.auth_crud import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])
