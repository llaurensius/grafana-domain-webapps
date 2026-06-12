import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.services.incident import IncidentService

logger = logging.getLogger("domain_monitor.scheduler")

scheduler = BackgroundScheduler()

def sync_metrics_job():
    """
    Job synchronous yang membungkus pemanggilan asinkronus ke IncidentService.
    """
    logger.info("Memulai background job sync status domain...")
    db = SessionLocal()
    try:
        # Menjalankan pemrosesan sync asinkronus dalam event loop baru
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(IncidentService.process_domain_status_sync(db))
        loop.close()
        
        logger.info(f"Background job selesai: {result}")
    except Exception as e:
        logger.error(f"Error pada background job sync status domain: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        # Jalankan job setiap 60 detik (1 menit)
        scheduler.add_job(sync_metrics_job, 'interval', seconds=60, id='sync_metrics_job_id')
        scheduler.start()
        logger.info("Background scheduler BERHASIL dijalankan.")
        
        # Jalankan sinkronisasi pertama kali secara langsung saat startup
        # (dijalankan di background thread agar tidak menghalangi startup FastAPI)
        scheduler.add_job(sync_metrics_job, 'date', id='sync_initial_run')

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler BERHASIL dihentikan.")
