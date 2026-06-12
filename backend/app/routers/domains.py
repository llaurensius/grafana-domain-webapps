import pandas as pd
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
import time
from app.schemas.domain import DomainResponse, DomainCreate, DomainUpdate, BulkDeleteRequest
from app.services.domain_service import DomainService

router = APIRouter()

@router.get("/", response_model=List[DomainResponse])
async def get_all_domains(db: Session = Depends(get_db)):
    service = DomainService(db)
    domains = service.repo.get_all()
    
    from app.services.prometheus_service import PrometheusService
    metrics = await PrometheusService.get_cached_metrics()
    
    probe_status_map = {}
    ssl_info_map = {}
    error_info_map = {}
    
    def norm_url(u):
        return u.rstrip('/') if u else ''
    
    if metrics is not None:
        for result in metrics.get("success", []):
            url_key = norm_url(result.get('metric', {}).get('instance'))
            probe_status_map[url_key] = int(result.get('value', [0, "0"])[1])
            
        current_time = time.time()
        for result in metrics.get("ssl", []):
            url_key = norm_url(result.get('metric', {}).get('instance'))
            expiry_timestamp = float(result.get('value', [0, "0"])[1])
            days_left = int((expiry_timestamp - current_time) / 86400)
            if days_left < 0:
                ssl_info_map[url_key] = "Expired"
            elif days_left <= 14:
                ssl_info_map[url_key] = f"Warning: {days_left} days left"
            else:
                ssl_info_map[url_key] = f"Valid ({days_left} days)"
                
        status_code_map = {}
        for result in metrics.get("status_code", []):
            url_key = norm_url(result.get('metric', {}).get('instance'))
            status_code_map[url_key] = float(result.get('value', [0, "0"])[1])

        dns_map = {}
        for result in metrics.get("dns", []):
            url_key = norm_url(result.get('metric', {}).get('instance'))
            dns_map[url_key] = float(result.get('value', [0, "0"])[1])

        ip_hash_map = {}
        for result in metrics.get("ip_hash", []):
            url_key = norm_url(result.get('metric', {}).get('instance'))
            ip_hash_map[url_key] = float(result.get('value', [0, "0"])[1])

        for url_key, success in probe_status_map.items():
            if success == 1:
                continue
            status_code = status_code_map.get(url_key, 0)
            dns_time = dns_map.get(url_key, 0)
            ip_hash = ip_hash_map.get(url_key, 0)
            
            if ip_hash == 0:
                error_info_map[url_key] = "DNS_PROBE_FINISHED_NXDOMAIN"
            elif status_code == 0:
                error_info_map[url_key] = "ERR_CONNECTION_REFUSED"
            elif status_code == 404:
                error_info_map[url_key] = "404 Page Not Found"
            elif status_code == 403:
                error_info_map[url_key] = "403 Forbidden"
            elif status_code == 500:
                error_info_map[url_key] = "500 Internal Server Error"
            elif status_code == 502:
                error_info_map[url_key] = "502 Bad Gateway"
            elif status_code == 503:
                error_info_map[url_key] = "503 Service Unavailable. The server is temporarily unable to service your request due to maintenance downtime or capacity problems."
            elif 400 <= status_code < 500:
                error_info_map[url_key] = f"{int(status_code)} Client Error"
            elif status_code >= 500:
                error_info_map[url_key] = f"{int(status_code)} Server Error"
            else:
                error_info_map[url_key] = "Unknown Error"
    # Load active incidents mapping
    from app.models.incident import Incident
    active_incidents = db.query(Incident).filter(Incident.status == "ACTIVE").all()
    active_incidents_map = {inc.domain_id: inc for inc in active_incidents}

    result_list = []
    for d in domains:
        n_url = norm_url(d.url)
        if not d.is_active:
            status = "UNMONITORED"
            ssl_info = "N/A"
            error_info = None
        else:
            if n_url not in probe_status_map:
                status = "PENDING"
            else:
                success = probe_status_map.get(n_url, 0)
                status = "UP" if success == 1 else "DOWN"
                
            ssl_info = ssl_info_map.get(n_url, "N/A") if n_url.startswith("https") else "HTTP (No SSL)"
            
            error_info = None
            if status == "DOWN":
                inc = active_incidents_map.get(d.id)
                if inc and inc.error_type:
                    error_info = inc.error_type
                else:
                    error_info = error_info_map.get(n_url)
            
        result_list.append(DomainResponse(
            id=d.id,
            url=d.url,
            name=d.name,
            is_active=d.is_active,
            created_at=d.created_at,
            status=status,
            ssl_info=ssl_info,
            error_info=error_info
        ))
    return result_list

@router.post("/", response_model=DomainResponse)
def create_domain(domain: DomainCreate, db: Session = Depends(get_db)):
    service = DomainService(db)
    return service.create_domain(domain)

@router.put("/{domain_id}", response_model=DomainResponse)
def update_domain(domain_id: int, domain: DomainUpdate, db: Session = Depends(get_db)):
    service = DomainService(db)
    updated = service.update_domain(domain_id, domain)
    if not updated:
        raise HTTPException(status_code=404, detail="Domain not found")
    return updated

@router.delete("/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    service = DomainService(db)
    deleted = service.delete_domain(domain_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Domain not found")
    return {"status": "ok"}

@router.post("/bulk-delete")
def bulk_delete_domains(req: BulkDeleteRequest, db: Session = Depends(get_db)):
    service = DomainService(db)
    service.bulk_delete_domains(req.ids)
    return {"status": "ok", "deleted": len(req.ids)}

@router.post("/import")
async def import_domains(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload .csv or .xlsx")
    
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        if 'name' not in df.columns or 'url' not in df.columns:
            raise HTTPException(status_code=400, detail="File must contain 'name' and 'url' columns")
            
        domains_in = []
        for _, row in df.iterrows():
            if pd.isna(row['name']) or pd.isna(row['url']):
                continue
            is_active = True
            if 'is_active' in df.columns and not pd.isna(row['is_active']):
                val = str(row['is_active']).lower()
                is_active = val in ('true', '1', 'yes', 'y', 't')
            
            domains_in.append(DomainCreate(
                name=str(row['name']).strip(),
                url=str(row['url']).strip(),
                is_active=is_active
            ))
            
        if not domains_in:
            raise HTTPException(status_code=400, detail="No valid domains found in file")
            
        service = DomainService(db)
        service.bulk_create_domains(domains_in)
        return {"status": "success", "imported": len(domains_in)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/export")
def export_domains(db: Session = Depends(get_db)):
    service = DomainService(db)
    domains = service.repo.get_all()
    
    data = []
    for d in domains:
        data.append({
            "name": d.name,
            "url": d.url,
            "is_active": d.is_active
        })
        
    df = pd.DataFrame(data)
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=domains.csv"
    return response

@router.delete("/wipe-all")
def wipe_all_database(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        db.execute(text("TRUNCATE TABLE domains RESTART IDENTITY CASCADE"))
        db.commit()
        return {"status": "ok", "message": "Database wiped successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
