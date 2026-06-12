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
    from app.config import settings
    # Fix Docker Race Condition by creating the directory and file before Prometheus starts trying to read it
    os.makedirs(os.path.dirname(settings.TARGETS_FILE_PATH), exist_ok=True)
    if not os.path.exists(settings.TARGETS_FILE_PATH):
        with open(settings.TARGETS_FILE_PATH, "w") as f:
            f.write("[]")
            
    start_scheduler()

# Register Routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(domains.router, prefix="/api/domains", tags=["domains"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(summary.router, prefix="/api/summary", tags=["summary"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
