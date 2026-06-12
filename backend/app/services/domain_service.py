from sqlalchemy.orm import Session
from app.repositories.domain_repo import DomainRepository
from app.schemas.domain import DomainCreate, DomainUpdate
from app.services.prometheus_service import PrometheusService

class DomainService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DomainRepository(db)

    def trigger_prometheus_sync(self):
        active_domains = self.repo.get_active()
        urls = [d.url for d in active_domains]
        PrometheusService.sync_targets_file(urls)

    def create_domain(self, domain_in: DomainCreate):
        domain = self.repo.create(domain_in)
        self.trigger_prometheus_sync()
        return domain

    def bulk_create_domains(self, domains_in: list[DomainCreate]):
        domains = self.repo.bulk_create(domains_in)
        self.trigger_prometheus_sync()
        return domains

    def update_domain(self, domain_id: int, domain_in: DomainUpdate):
        domain = self.repo.get_by_id(domain_id)
        if not domain:
            return None
        updated_domain = self.repo.update(domain, domain_in)
        self.trigger_prometheus_sync()
        return updated_domain

    def delete_domain(self, domain_id: int):
        domain = self.repo.get_by_id(domain_id)
        if domain:
            self.repo.delete(domain)
            self.trigger_prometheus_sync()
        return domain

    def bulk_delete_domains(self, domain_ids: list[int]):
        self.repo.bulk_delete(domain_ids)
        self.trigger_prometheus_sync()
