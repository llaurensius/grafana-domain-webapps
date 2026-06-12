from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date, datetime

class KPISummary(BaseModel):
    total_domains: int
    active_domains: int
    up_domains: int
    down_domains: int
    active_incidents: int
    downtime_today_seconds: int
    prometheus_status: str  # online, offline, no_data

class AffectedDomain(BaseModel):
    domain_id: int
    domain_name: str
    target_url: str
    incident_count: int
    total_downtime_seconds: int

class PeriodSummary(BaseModel):
    period: str  # "daily", "weekly", "monthly"
    start_date: date
    end_date: date
    total_incidents: int
    total_downtime_seconds: int
    top_affected_domains: List[AffectedDomain]
    error_distribution: Dict[str, int]
