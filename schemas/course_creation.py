from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

# ========================
# PORTAL SCHEMAS
# ========================

class PortalCreate(BaseModel):
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    status: str
    deadline_date: Optional[date]


class PortalUpdate(BaseModel):
    portal_id: int
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    deadline_date: Optional[date]


class PortalStatusUpdate(BaseModel):
    portal_id: int
    status: str


# ========================
# MODULE SCHEMAS
# ========================

class ModuleCreate(BaseModel):
    portal_id: int
    title: str
    module_goal: Optional[str] = None


class ModuleUpdate(BaseModel):
    module_id: int
    title: Optional[str] = None
    module_goal: Optional[str] = None


# ========================
# LESSON SCHEMAS
# ========================

class LessonCreate(BaseModel):
    module_id: int
    title: str
    content_type: Optional[str] = None
    content_url: Optional[str] = None


class LessonUpdate(BaseModel):
    lesson_id: int
    content_url: Optional[str] = None


class LessonComplete(BaseModel):
    lesson_id: int
