import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.incident_service import IncidentService

logger = logging.getLogger("uvicorn.scheduler")

scheduler = AsyncIOScheduler()


def sync_metrics_job():
    """
    Job yang dijalankan APScheduler secara berkala.

    PENTING — Mengapa ini bukan `async def`:
    APScheduler dengan AsyncIOScheduler akan menjalankan fungsi `def` biasa
    (sinkronus) di dalam Thread Pool Executor terpisah secara otomatis.
    Hal ini mencegah operasi blocking (SQLAlchemy commit, query DB) dari
    menahan Single-Threaded Event Loop utama FastAPI, sehingga endpoint
    /api/ tetap responsif bahkan saat scheduler sedang bekerja keras.
    """
    db = SessionLocal()
    try:
        service = IncidentService(db)
        service.process_metrics()
    except Exception as e:
        logger.error(f"[Scheduler] Job sync_metrics gagal: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    # misfire_grace_time: jika job tertunda (misal server sibuk), masih boleh
    # dijalankan dalam 60 detik setelah waktu yang dijadwalkan. Setelah itu skip.
    scheduler.add_job(sync_metrics_job, "interval", minutes=1, misfire_grace_time=60)
    scheduler.start()
    logger.info("[Scheduler] Background job 'sync_metrics_job' started (interval: 1 menit).")
