from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from typing import Optional

from app.database import get_db
from app.schemas.report import ReportPreviewResponse
from app.services.report_service import generate_report_data, generate_excel_bytes

router = APIRouter()

@router.get("/preview", response_model=ReportPreviewResponse)
def preview_report(
    period: str = Query(..., description="daily, weekly, monthly"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD for daily"),
    month: Optional[str] = Query(None, description="YYYY-MM for weekly or monthly"),
    week: Optional[int] = Query(None, description="1-5 for weekly"),
    search: Optional[str] = Query(None, description="Search domain or url"),
    status: Optional[str] = Query(None, description="UP or DOWN"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        data = generate_report_data(db, period, date, month, week)
        
        # Apply filters
        if search:
            s = search.lower()
            data = [d for d in data if s in d['domain_name'].lower() or s in d['url'].lower()]
        if status:
            data = [d for d in data if d['status'].upper() == status.upper()]
            
        total = len(data)
        paginated_data = data[skip : skip + limit]
        return {"total": total, "data": paginated_data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export")
def export_report(
    period: str = Query(..., description="daily, weekly, monthly"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD for daily"),
    month: Optional[str] = Query(None, description="YYYY-MM for weekly or monthly"),
    week: Optional[int] = Query(None, description="1-5 for weekly"),
    search: Optional[str] = Query(None, description="Search domain or url"),
    status: Optional[str] = Query(None, description="UP or DOWN"),
    db: Session = Depends(get_db)
):
    try:
        data = generate_report_data(db, period, date, month, week)
        
        # Apply filters
        if search:
            s = search.lower()
            data = [d for d in data if s in d['domain_name'].lower() or s in d['url'].lower()]
        if status:
            data = [d for d in data if d['status'].upper() == status.upper()]
            
        file_bytes = generate_excel_bytes(data)
        
        filename = f"report_{period}"
        if period == 'daily' and date:
            filename += f"_{date}"
        elif period == 'weekly' and month and week:
            filename += f"_{month}_week{week}"
        elif period == 'monthly' and month:
            filename += f"_{month}"
        filename += ".xlsx"
        
        return StreamingResponse(
            file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
