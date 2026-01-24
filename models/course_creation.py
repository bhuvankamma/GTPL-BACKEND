from sqlalchemy import (
    Column,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from sqlalchemy.sql import func
from database_B import Base
from database import Base



# =====================================================
# PORTAL MODEL
# =====================================================

class Portal(Base):
    __tablename__ = "portal" 

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    category = Column(Text)
    description = Column(Text)
    status = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline_date = Column(Date, nullable=True)

    modules = relationship("Module", back_populates="portal")


# =====================================================
# MODULE MODEL
# =====================================================

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    portal_id = Column(Integer, ForeignKey("portal.id"))
    title = Column(Text, nullable=False)
    module_goal = Column(Text)          # ✅ INCLUDED
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    portal = relationship("Portal", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module")


# =====================================================
# LESSON MODEL
# =====================================================

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    title = Column(Text, nullable=False)
    content_type = Column(Text)
    content_url = Column(Text)
    content_link_status = Column(Text, default="Missing")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    module = relationship("Module", back_populates="lessons")
