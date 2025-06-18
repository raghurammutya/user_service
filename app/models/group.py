# Create a simple Group model for user_service
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from shared_architecture.db.base import Base

class Group(Base):
    __tablename__ = "groups"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("tradingdb.users.id"))
    
    # Simple relationships for user_service
    members = relationship("User", back_populates="group", foreign_keys="User.group_id")
    
    def __repr__(self):
        return f"<Group(id={self.id}, name='{self.name}')>"