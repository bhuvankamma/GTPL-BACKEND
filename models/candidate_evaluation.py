from sqlalchemy import Column, Integer, String, Boolean, Text
<<<<<<< HEAD
from database import Base   # 👈 USE YOUR EXISTING BASE
=======
from database_B import Base   # 👈 USE YOUR EXISTING BASE
>>>>>>> origin/feature/bhavani

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    email = Column(String)
    mobile = Column(String)
    position = Column(String)

    technical_skill = Column(Boolean)
    communication_skill = Column(Boolean)

    technical_feedback = Column(Text)
    communication_feedback = Column(Text)
    overall_feedback = Column(Text)

    report_file = Column(Text)
    status = Column(String)
