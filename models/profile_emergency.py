from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database_su import Base


class EmployeeEmergencyContact(Base):
    __tablename__ = "employee_emergency_contacts"

    # ==================================================
    # PRIMARY KEY
    # ==================================================
    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # EMPLOYEE REFERENCE
    # ==================================================
    emp_code = Column(
        String,
        ForeignKey("employees.emp_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional ORM relationship
    employee = relationship(
        "Employee",
        backref="emergency_contacts",
        passive_deletes=True,
    )

    # ==================================================
    # EMERGENCY CONTACT DETAILS
    # ==================================================
    name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)   # Father, Spouse, Friend
    phone = Column(String, nullable=False)
    alternate_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
