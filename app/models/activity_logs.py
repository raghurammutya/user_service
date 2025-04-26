from sqlalchemy import Column, Integer, String, DateTime
from shared_architecture.db import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String)
    timestamp = Column(DateTime)