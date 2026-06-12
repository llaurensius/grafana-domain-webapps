from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base
import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String, nullable=False)  # LOGIN, CREATE_DOMAIN, UPDATE_DOMAIN, DELETE_DOMAIN, SYNC
    action_detail = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
