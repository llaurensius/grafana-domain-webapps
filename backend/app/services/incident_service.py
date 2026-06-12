from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio
from app.repositories.incident_repo import IncidentRepository
from app.repositories.domain_repo import DomainRepository
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.prometheus_service import PrometheusService

class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.domain_repo = DomainRepository(db)

    async def process_metrics(self):
        """Processes metrics from Prometheus and updates incidents"""
        metrics = await PrometheusService.query_probe_metrics()
        
        if metrics is None:
            print("Prometheus is unreachable. Skipping metrics processing to avoid false resolutions.")
            return
            
        if len(metrics) == 0:
            print("Prometheus returned no data. Possibly targets are empty or Blackbox exporter is down.")
            return
            
        # Map domains by URL for fast lookup
        active_domains = {d.url: d for d in self.domain_repo.get_active()}
        
        now = datetime.now(timezone.utc)
        
        for result in metrics.get("success", []):
            metric = result.get('metric', {})
            instance_url = metric.get('instance')
            
            # Perhatikan: value array berbentuk [timestamp, "string_value"]
            probe_success = int(result.get('value', [0, "0"])[1])
            
            domain = active_domains.get(instance_url)
            if not domain:
                continue
                
            active_incident = self.incident_repo.get_active_incident(domain.id)
            
            if probe_success == 0: # Domain is DOWN
                if not active_incident:
                    # Determine Error Type
                    error_type = await PrometheusService.query_error_classification(instance_url)
                    
                    # Fetch exact error from blackbox logs
                    exact_error = await PrometheusService.fetch_exact_error(instance_url)
                    if exact_error and "Unknown error" not in exact_error and "Fetch log error" not in exact_error:
                        error_type = exact_error
                    
                    # Create new ACTIVE incident
                    incident_in = IncidentCreate(
                        domain_id=domain.id,
                        status="ACTIVE",
                        qualifies_as_downtime=False,
                        error_type=error_type,
                        start_time=now
                    )
                    self.incident_repo.create(incident_in)
                else:
                    # Check if duration > 5 minutes (300 seconds, buffered to 295s for drift)
                    duration_seconds = int((now - active_incident.start_time.replace(tzinfo=timezone.utc)).total_seconds())
                    if duration_seconds >= 295 and not active_incident.qualifies_as_downtime:
                        # Upgrade to confirmed downtime
                        self.incident_repo.update(
                            active_incident,
                            IncidentUpdate(qualifies_as_downtime=True)
                        )
            
            elif probe_success == 1: # Domain is UP
                if active_incident:
                    # Resolve the incident
                    duration_seconds = int((now - active_incident.start_time.replace(tzinfo=timezone.utc)).total_seconds())
                    qualifies = active_incident.qualifies_as_downtime or (duration_seconds >= 295)
                    
                    self.incident_repo.update(
                        active_incident,
                        IncidentUpdate(
                            end_time=now,
                            duration_seconds=duration_seconds,
                            status="RESOLVED",
                            qualifies_as_downtime=qualifies
                        )
                    )
