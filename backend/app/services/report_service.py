import zoneinfo
from datetime import datetime, timedelta
from typing import Tuple, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_
from collections import defaultdict
import pandas as pd
from io import BytesIO

from app.models.domain import Domain
from app.models.incident import Incident

TZ_JKT = zoneinfo.ZoneInfo("Asia/Jakarta")

def get_daily_bounds(date_str: str) -> Tuple[datetime, datetime, str]:
    # format: YYYY-MM-DD
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start = dt.replace(hour=0, minute=0, second=0, tzinfo=TZ_JKT)
    end = dt.replace(hour=23, minute=59, second=59, tzinfo=TZ_JKT)
    return start, end, date_str

def get_monthly_bounds(month_str: str) -> Tuple[datetime, datetime, str]:
    # format: YYYY-MM
    dt = datetime.strptime(month_str, "%Y-%m")
    year = dt.year
    month = dt.month
    
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_JKT)
    
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=TZ_JKT)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=TZ_JKT)
        
    end = next_month - timedelta(seconds=1)
    
    return start, end, dt.strftime("%B %Y")

def get_weekly_bounds(month_str: str, week: int) -> Tuple[datetime, datetime, str]:
    dt = datetime.strptime(month_str, "%Y-%m")
    year = dt.year
    month = dt.month
    
    first_day = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_JKT)
    first_day_weekday = first_day.weekday() # 0 = Mon, 6 = Sun
    
    days_to_sunday = 6 - first_day_weekday
    end_of_week_1 = first_day + timedelta(days=days_to_sunday)
    end_of_week_1 = end_of_week_1.replace(hour=23, minute=59, second=59)
    
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=TZ_JKT)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=TZ_JKT)
    last_day_of_month = next_month - timedelta(seconds=1)

    if week == 1:
        end = min(end_of_week_1, last_day_of_month)
        return first_day, end, f"Week 1, {dt.strftime('%B %Y')}"
    
    weeks_to_add = week - 1
    start_of_week = first_day + timedelta(days=days_to_sunday + 1 + (weeks_to_add - 1) * 7)
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0)
    
    end_of_week = start_of_week + timedelta(days=6)
    end_of_week = end_of_week.replace(hour=23, minute=59, second=59)
    
    if start_of_week > last_day_of_month:
        raise ValueError(f"Week {week} does not exist in {month_str}")
        
    end = min(end_of_week, last_day_of_month)
    
    return start_of_week, end, f"Week {week}, {dt.strftime('%B %Y')}"


def generate_report_data(db: Session, period: str, date: str = None, month: str = None, week: int = None) -> List[Dict]:
    if period == 'daily':
        if not date:
            raise ValueError("date parameter is required for daily period")
        start_date, end_date, label = get_daily_bounds(date)
    elif period == 'monthly':
        if not month:
            raise ValueError("month parameter is required for monthly period")
        start_date, end_date, label = get_monthly_bounds(month)
    elif period == 'weekly':
        if not month or not week:
            raise ValueError("month and week parameters are required for weekly period")
        start_date, end_date, label = get_weekly_bounds(month, week)
    else:
        raise ValueError(f"Invalid period: {period}")

    # Helper to calculate overlap duration
    now = datetime.now(TZ_JKT)
    period_end_for_calc = min(end_date, now)

    domains = db.query(Domain).all()
    
    incidents = db.query(Incident).filter(
        Incident.start_time <= end_date,
        or_(Incident.end_time >= start_date, Incident.end_time.is_(None))
    ).all()
    
    incident_map = defaultdict(list)
    for inc in incidents:
        incident_map[inc.domain_id].append(inc)
        
    # Get current status from Prometheus Cache safely
    from app.services.prometheus_service import PrometheusService
    import asyncio
    status_map = {}
    try:
        metrics = asyncio.run(PrometheusService.get_cached_metrics())
        if metrics and "success" in metrics:
            for item in metrics["success"]:
                url = item.get("metric", {}).get("instance")
                val = item.get("value", [None, "0"])[1]
                if url:
                    status_map[url] = "UP" if val == "1" else "DOWN"
    except Exception as e:
        print("Error fetching prometheus status:", e)
        
    data = []
    
    for d in domains:
        incs = incident_map.get(d.id, [])
        current_status = status_map.get(d.url, "UP") # Fallback UP if not found
        
        if not incs:
            data.append({
                "domain_name": d.name,
                "url": d.url,
                "status": current_status,
                "error_summary": "-",
                "total_downtime": "0s",
                "incident_count": 0,
                "last_checked": start_date.strftime("%Y-%m-%d %H:%M:%S") + " (Period Start)",
                "period_type": period.capitalize(),
                "period_label": label,
                "source": "DB"
            })
        else:
            total_duration_seconds = 0
            error_counts = defaultdict(int)
            
            for inc in incs:
                # Accumulate downtime (only overlapping the period if we want strict bounds, 
                # but MVP usually just sums duration_seconds or calculates ongoing)
                if inc.duration_seconds is not None:
                    total_duration_seconds += inc.duration_seconds
                else:
                    # Ongoing incident
                    inc_start = inc.start_time.astimezone(TZ_JKT) if inc.start_time.tzinfo else inc.start_time.replace(tzinfo=TZ_JKT)
                    total_duration_seconds += max(0, (period_end_for_calc - inc_start).total_seconds())
                
                err_type = inc.error_type or "Unknown"
                error_counts[err_type] += 1
                
            # Format total downtime
            td_int = int(total_duration_seconds)
            if td_int == 0:
                dur_str = "0s"
            else:
                h = td_int // 3600
                m = (td_int % 3600) // 60
                s = td_int % 60
                dur_str = ""
                if h > 0: dur_str += f"{h}h "
                if m > 0 or h > 0: dur_str += f"{m}m "
                dur_str += f"{s}s"
                dur_str = dur_str.strip()
                
            # Format error summary
            error_summary_parts = []
            for err_type, count in error_counts.items():
                error_summary_parts.append(f"{err_type} ({count}x)")
            error_summary = ", ".join(error_summary_parts)
            
            data.append({
                "domain_name": d.name,
                "url": d.url,
                "status": current_status,
                "error_summary": error_summary,
                "total_downtime": dur_str,
                "incident_count": len(incs),
                "last_checked": "-",
                "period_type": period.capitalize(),
                "period_label": label,
                "source": "DB"
            })
            
    data.sort(key=lambda x: x['domain_name'])
    return data

def generate_excel_bytes(data: List[Dict]) -> BytesIO:
    df = pd.DataFrame(data)
    
    columns = {
        "domain_name": "Domain Name",
        "url": "URL",
        "status": "Current Status",
        "error_summary": "Error Summary",
        "total_downtime": "Total Downtime",
        "incident_count": "Incident Count",
        "last_checked": "Last Checked",
        "period_type": "Period Type",
        "period_label": "Period Label",
        "source": "Source"
    }
    
    if not df.empty:
        df = df.rename(columns=columns)
    else:
        df = pd.DataFrame(columns=list(columns.values()))
        
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Monitoring Report')
    output.seek(0)
    return output
