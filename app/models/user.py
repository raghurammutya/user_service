# Create a simple User model for user_service
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared_architecture.db.base import Base
from shared_architecture.enums import UserRole

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True)
    group_id = Column(Integer, ForeignKey("tradingdb.groups.id"))
    role = Column(String(50), default=UserRole.VIEWER.value, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Simple relationships for user_service
    group = relationship("Group", back_populates="members", foreign_keys=[group_id])
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
