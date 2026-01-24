from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from database_su import Base
from datetime import date


class EmployeeReportingHierarchy(Base):
    __tablename__ = "employee_reporting_hierarchy"

    # ==================================================
    # PRIMARY KEY
    # ==================================================
    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # EMPLOYEE REFERENCES
    # ==================================================
    emp_code = Column(
        String,
        ForeignKey("employees.emp_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    manager_emp_code = Column(
        String,
        ForeignKey("employees.emp_code", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==================================================
    # REPORTING DETAILS
    # ==================================================
    level = Column(Integer, nullable=False)  # e.g. 1, 2, 3
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

    # ==================================================
    # SYSTEM
    # ==================================================
    created_at = Column(Date, default=date.today)

    # ==================================================
    # ORM RELATIONSHIPS (OPTIONAL BUT RECOMMENDED)
    # ==================================================
    employee = relationship(
        "Employee",
        foreign_keys=[emp_code],
        lazy="joined",
    )

    manager = relationship(
        "Employee",
        foreign_keys=[manager_emp_code],
        lazy="joined",
    )
