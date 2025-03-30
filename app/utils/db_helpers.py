from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

def commit_with_handling(db: Session):
    """
    Commit changes to the database with error handling.
    """
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database Integrity Error: {e}")