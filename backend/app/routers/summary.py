from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.incident import Incident
import csv
from io import StringIO

router = APIRouter()

@router.get("/stats")
def get_summary_stats(period: str = "daily", db: Session = Depends(get_db)):
    """Returns basic stats based on period: daily, weekly, monthly"""
    now_utc = datetime.now(timezone.utc)
    
    # Calculate local start time based on Jakarta timezone
    import zoneinfo
    tz = zoneinfo.ZoneInfo("Asia/Jakarta")
    now_local = now_utc.astimezone(tz)
    
    if period == "daily":
        start_date_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date_local.astimezone(timezone.utc)
    elif period == "weekly":
        start_date_local = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date_local.astimezone(timezone.utc)
    else:
        start_date_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date_local.astimezone(timezone.utc)

    # Calculate downtime metrics (only qualifies_as_downtime = True)
    total_incidents = db.query(Incident).filter(
        Incident.qualifies_as_downtime == True,
        Incident.start_time >= start_date
    ).count()

    total_downtime_seconds = db.query(func.sum(Incident.duration_seconds)).filter(
        Incident.qualifies_as_downtime == True,
        Incident.status == "RESOLVED",
        Incident.start_time >= start_date
    ).scalar() or 0

    return {
        "period": period,
        "total_incidents": total_incidents,
        "total_downtime_minutes": round(total_downtime_seconds / 60, 2)
    }

@router.get("/export")
def export_incidents_csv(db: Session = Depends(get_db)):
    """Exports all incidents to a CSV file"""
    incidents = db.query(Incident).order_by(Incident.start_time.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Domain ID', 'Start Time', 'End Time', 'Duration (s)', 'Status', 'Is True Downtime', 'Error Type'])
    
    for inc in incidents:
        writer.writerow([
            inc.id, inc.domain_id, 
            inc.start_time.isoformat() if inc.start_time else '',
            inc.end_time.isoformat() if inc.end_time else '',
            inc.duration_seconds, inc.status, 
            inc.qualifies_as_downtime, inc.error_type
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=incidents.csv"}
    )
