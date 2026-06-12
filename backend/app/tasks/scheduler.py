from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.incident_service import IncidentService

scheduler = AsyncIOScheduler()

async def sync_metrics_job():
    db = SessionLocal()
    try:
        service = IncidentService(db)
        await service.process_metrics()
    finally:
        db.close()

def start_scheduler():
    # Job runs every 1 minute
    scheduler.add_job(sync_metrics_job, "interval", minutes=1, misfire_grace_time=60)
    scheduler.start()
