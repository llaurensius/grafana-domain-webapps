from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, domains, incidents, summary, health, reports
from app.tasks.scheduler import start_scheduler
from app.config import settings

# Buat tabel di PostgreSQL (untuk dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

import os
origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
# FastAPI forbids allow_origins=["*"] when allow_credentials=True. 
# For wildcard, we must either not use allow_credentials=True or handle it.
# If MVP LAN usage relies on wildcard, we can use allow_origin_regex.

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else [],
    allow_origin_regex=".*" if origins == ["*"] else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start background cron tasks
@app.on_event("startup")
def startup_event():
    import os
    import logging
    from app.config import settings
    from app.database import SessionLocal
    from app.repositories.domain_repo import DomainRepository
    from app.services.prometheus_service import PrometheusService

    logger = logging.getLogger("uvicorn.startup")

    # Pastikan direktori /shared selalu ada sebelum apapun
    os.makedirs(os.path.dirname(settings.TARGETS_FILE_PATH), exist_ok=True)

    # ─── SELF-HEALING: Rebuild file target dari Database (Source of Truth) ───
    # Jika file target hilang (volume Docker terhapus, kontainer baru) atau
    # isinya tidak sinkron, kita tidak menulis array kosong [].
    # Backend menjadi "sumber kebenaran" dan merekonstruksi konfigurasi Prometheus
    # langsung dari data domain aktif yang ada di PostgreSQL.
    db = SessionLocal()
    try:
        domain_repo = DomainRepository(db)
        active_domains = domain_repo.get_active()  # Ambil semua domain aktif
        active_urls = [d.url for d in active_domains]

        PrometheusService.sync_targets_file(active_urls)
        logger.info(
            f"[Self-Healing] File target Prometheus dibangun ulang: "
            f"{len(active_urls)} domain aktif ditulis ke {settings.TARGETS_FILE_PATH}"
        )
    except Exception as e:
        # Jangan crash saat startup. Log error, tulis file kosong sebagai fallback.
        logger.error(f"[Self-Healing] Gagal rebuild file target dari DB: {e}")
        logger.warning("Melanjutkan startup dengan file target kosong sebagai fallback.")
        try:
            PrometheusService.sync_targets_file([])
        except Exception:
            pass  # Jika bahkan menulis [] pun gagal, scheduler akan mencoba lagi nanti
    finally:
        db.close()
    # ─────────────────────────────────────────────────────────────────────────

    start_scheduler()


# Register Routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(domains.router, prefix="/api/domains", tags=["domains"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(summary.router, prefix="/api/summary", tags=["summary"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
