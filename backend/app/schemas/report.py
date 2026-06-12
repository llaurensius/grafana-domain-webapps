from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ReportRow(BaseModel):
    domain_name: str
    url: str
    status: str
    error_summary: str
    total_downtime: str
    incident_count: int
    last_checked: str
    period_type: str
    period_label: str
    source: str

class ReportPreviewResponse(BaseModel):
    total: int
    data: List[ReportRow]
