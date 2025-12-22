from sqlalchemy.orm import Session
from models.candidate_evaluation import Candidate
from schemas.candidate_evaluation import CandidateCreate, CandidateUpdate


def create_candidate(db: Session, data: CandidateCreate):
    status = "Selected" if data.technical_skill and data.communication_skill else "Rejected"

    candidate = Candidate(
        **data.dict(),
        status=status
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def get_candidate(db: Session, candidate_id: int):
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()


def get_all_candidates(db: Session):
    return db.query(Candidate).all()


def update_candidate(db: Session, candidate_id: int, data: CandidateUpdate):
    candidate = get_candidate(db, candidate_id)
    if not candidate:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(candidate, key, value)

    db.commit()
    db.refresh(candidate)
    return candidate


def delete_candidate(db: Session, candidate_id: int):
    candidate = get_candidate(db, candidate_id)
    if not candidate:
        return False

    db.delete(candidate)
    db.commit()
    return True
