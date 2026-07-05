import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.domain import DomainResponse, DomainCreate, DomainUpdate, BulkDeleteRequest
from app.services.domain_service import DomainService

router = APIRouter()


@router.get("/", response_model=List[DomainResponse])
async def get_all_domains(db: Session = Depends(get_db)):
    """Mengambil semua domain beserta status real-time dari Prometheus."""
    service = DomainService(db)
    return await service.get_domains_with_status()


@router.post("/", response_model=DomainResponse)
def create_domain(domain: DomainCreate, db: Session = Depends(get_db)):
    """Membuat domain baru."""
    service = DomainService(db)
    return service.create_domain(domain)


@router.put("/{domain_id}", response_model=DomainResponse)
def update_domain(domain_id: int, domain: DomainUpdate, db: Session = Depends(get_db)):
    """Memperbarui data domain berdasarkan ID."""
    service = DomainService(db)
    updated = service.update_domain(domain_id, domain)
    if not updated:
        raise HTTPException(status_code=404, detail="Domain not found")
    return updated


@router.delete("/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    """Menghapus domain berdasarkan ID."""
    service = DomainService(db)
    deleted = service.delete_domain(domain_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Domain not found")
    return {"status": "ok"}


@router.post("/bulk-delete")
def bulk_delete_domains(req: BulkDeleteRequest, db: Session = Depends(get_db)):
    """Menghapus banyak domain sekaligus berdasarkan daftar ID."""
    service = DomainService(db)
    service.bulk_delete_domains(req.ids)
    return {"status": "ok", "deleted": len(req.ids)}


@router.post("/import")
async def import_domains(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Mengimpor domain dari file CSV.
    File harus memiliki kolom: name, url, dan opsional is_active.
    Menggunakan modul csv bawaan Python (lebih ringan dari pandas).
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a .csv file.",
        )

    try:
        contents = await file.read()
        decoded = contents.decode("utf-8-sig")  # utf-8-sig untuk menangani BOM dari Excel
        reader = csv.DictReader(io.StringIO(decoded))

        if reader.fieldnames is None or "name" not in reader.fieldnames or "url" not in reader.fieldnames:
            raise HTTPException(
                status_code=400,
                detail="File must contain 'name' and 'url' columns.",
            )

        domains_in: List[DomainCreate] = []
        for row in reader:
            name = (row.get("name") or "").strip()
            url = (row.get("url") or "").strip()
            if not name or not url:
                continue  # Lewati baris kosong/tidak valid

            is_active_raw = str(row.get("is_active", "true")).lower()
            is_active = is_active_raw in ("true", "1", "yes", "y", "t")

            domains_in.append(DomainCreate(name=name, url=url, is_active=is_active))

        if not domains_in:
            raise HTTPException(status_code=400, detail="No valid domains found in file.")

        service = DomainService(db)
        service.bulk_create_domains(domains_in)
        return {"status": "success", "imported": len(domains_in)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")


@router.get("/export")
def export_domains(db: Session = Depends(get_db)):
    """Mengekspor semua domain ke format CSV."""
    service = DomainService(db)
    domains = service.repo.get_all()

    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["name", "url", "is_active"])
    writer.writeheader()
    for d in domains:
        writer.writerow({"name": d.name, "url": d.url, "is_active": d.is_active})

    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=domains.csv"
    return response


@router.delete("/wipe-all")
def wipe_all_database(db: Session = Depends(get_db)):
    """Menghapus seluruh data domain dari database (operasi destruktif)."""
    from sqlalchemy import text
    try:
        db.execute(text("TRUNCATE TABLE domains RESTART IDENTITY CASCADE"))
        db.commit()
        return {"status": "ok", "message": "Database wiped successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

