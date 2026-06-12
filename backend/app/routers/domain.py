from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.domain import DomainCreate, DomainUpdate, DomainResponse
from app.repositories.domain import DomainRepository
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.auth import AuthService
from app.services.prometheus import PrometheusService
from typing import List, Optional

router = APIRouter(prefix="/api/domains", tags=["Domains"])

def write_audit_log(db: Session, user_id: int, action: str, detail: str):
    log = AuditLog(user_id=user_id, action_type=action, action_detail=detail)
    db.add(log)
    db.commit()

@router.get("/", response_model=List[DomainResponse])
def get_domains(
    active_only: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    repo = DomainRepository(db)
    return repo.get_all(active_only=active_only)

@router.post("/", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
def create_domain(
    domain_in: DomainCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    repo = DomainRepository(db)
    
    # Cek apakah target url sudah ada
    existing = repo.get_by_url(domain_in.target_url)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain target URL sudah terdaftar."
        )
        
    domain = repo.create(domain_in)
    
    # Sinkronisasi ke targets.json Prometheus
    PrometheusService.sync_prometheus_targets(db)
    
    # Catat audit log
    write_audit_log(db, current_user.id, "CREATE_DOMAIN", f"Menambahkan domain: {domain.name} ({domain.target_url})")
    
    return domain

@router.put("/{domain_id}", response_model=DomainResponse)
def update_domain(
    domain_id: int,
    domain_in: DomainUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    repo = DomainRepository(db)
    domain = repo.get_by_id(domain_id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain tidak ditemukan."
        )
        
    # Jika mengubah url, pastikan tidak duplikat dengan domain lain
    if domain_in.target_url and domain_in.target_url != domain.target_url:
        existing = repo.get_by_url(domain_in.target_url)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain target URL sudah terdaftar."
            )
            
    old_name = domain.name
    old_url = domain.target_url
    
    updated_domain = repo.update(domain, domain_in)
    
    # Sinkronisasi ke targets.json Prometheus
    PrometheusService.sync_prometheus_targets(db)
    
    # Catat audit log
    write_audit_log(
        db, 
        current_user.id, 
        "UPDATE_DOMAIN", 
        f"Mengubah domain ID {domain_id} dari {old_name} ({old_url}) menjadi {updated_domain.name} ({updated_domain.target_url})"
    )
    
    return updated_domain

@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    repo = DomainRepository(db)
    domain = repo.get_by_id(domain_id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain tidak ditemukan."
        )
        
    name = domain.name
    url = domain.target_url
    
    repo.delete(domain)
    
    # Sinkronisasi ke targets.json Prometheus
    PrometheusService.sync_prometheus_targets(db)
    
    # Catat audit log
    write_audit_log(db, current_user.id, "DELETE_DOMAIN", f"Menghapus domain: {name} ({url})")
    
    return None

@router.post("/sync", status_code=status.HTTP_200_OK)
def trigger_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Endpoint manual untuk memicu penulisan file targets.json
    """
    success = PrometheusService.sync_prometheus_targets(db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal menyinkronkan target ke Prometheus."
        )
    write_audit_log(db, current_user.id, "SYNC_TARGETS", "Memicu sinkronisasi manual targets Prometheus.")
    return {"message": "Berhasil menyinkronkan targets ke Prometheus."}
