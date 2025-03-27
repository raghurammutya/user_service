
from sqlalchemy import create_engine, Column,Boolean, Integer, Float,String, Date, DateTime, ForeignKey, UniqueConstraint, Text
from ..database import Base
class SymbolUpdateStatus(Base):
    __tablename__ = "symbols_update_status"
    broker_name = Column(String, primary_key=True)
    update_date = Column(Date, primary_key=True)
    update_time = Column(DateTime)
    