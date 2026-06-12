from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), default=func.now(), index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String, default="ACTIVE", index=True) # ACTIVE, RESOLVED
    qualifies_as_downtime = Column(Boolean, default=False, index=True)
    error_type = Column(String, nullable=True) # e.g., DNS Error, Connection Error, HTTP 5xx
