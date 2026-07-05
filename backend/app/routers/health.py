from fastapi import APIRouter
from app.services.prometheus_service import PrometheusService

router = APIRouter()

@router.get("/")
async def health_check():
    prom_health = await PrometheusService.check_health()
    status = "ok" if prom_health["status"] == "UP" else "degraded"
    
    return {
        "status": status,
        "service": "Monitoring Backend",
        "prometheus_connection": prom_health["status"],
        "prometheus_has_data": prom_health["has_data"]
    }


