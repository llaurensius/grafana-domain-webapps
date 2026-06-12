import json
import os
import logging
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.domain import Domain
from typing import List, Dict, Any, Optional

logger = logging.getLogger("domain_monitor.prometheus_service")

class PrometheusService:
    @staticmethod
    def sync_prometheus_targets(db: Session) -> bool:
        """
        Menulis semua domain aktif ke file JSON targets untuk Prometheus file_sd_configs.
        """
        try:
            # Ambil semua domain aktif dari DB
            active_domains = db.query(Domain).filter(Domain.active == True).all()
            
            targets_config = []
            for domain in active_domains:
                targets_config.append({
                    "targets": [domain.target_url],
                    "labels": {
                        "domain_id": str(domain.id),
                        "name": domain.name
                    }
                })
            
            # Tulis ke targets file
            file_path = settings.PROMETHEUS_TARGETS_FILE
            
            # Pastikan directory ada
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(targets_config, f, indent=2)
                
            logger.info(f"Berhasil mensinkronkan {len(active_domains)} target ke {file_path}")
            return True
        except Exception as e:
            logger.error(f"Gagal mensinkronkan target ke Prometheus: {str(e)}")
            return False

    @staticmethod
    async def check_prometheus_health() -> str:
        """
        Mengecek apakah Prometheus API online dan merespons.
        Mengembalikan 'online', 'offline', atau 'no_data'.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{settings.PROMETHEUS_URL}/-/healthy")
                if response.status_code == 200:
                    # Cek juga apakah ada data / endpoint query merespons
                    query_test = await client.get(f"{settings.PROMETHEUS_URL}/api/v1/query?query=up")
                    if query_test.status_code == 200:
                        return "online"
                    return "no_data"
                return "offline"
        except Exception:
            return "offline"

    @staticmethod
    async def query_prometheus_instant(query_string: str) -> Optional[List[Dict[str, Any]]]:
        """
        Melakukan kueri instan ke Prometheus HTTP API.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{settings.PROMETHEUS_URL}/api/v1/query"
                response = await client.get(url, params={"query": query_string})
                if response.status_code != 200:
                    logger.error(f"Prometheus API error {response.status_code}: {response.text}")
                    return None
                
                res_json = response.json()
                if res_json.get("status") == "success":
                    return res_json.get("data", {}).get("result", [])
                return None
        except Exception as e:
            logger.error(f"Gagal melakukan kueri ke Prometheus: {str(e)}")
            return None
            
    @classmethod
    async def get_latest_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """
        Mengambil status probe_success, HTTP status code, latency, dll. untuk seluruh domain.
        Menghasilkan dictionary berpola: { domain_id: { "probe_success": X, "status_code": Y, ... } }
        """
        metrics = {}
        
        # Query probe_success
        success_data = await cls.query_prometheus_instant('probe_success{job="blackbox"}')
        # Query http status code
        status_code_data = await cls.query_prometheus_instant('probe_http_status_code{job="blackbox"}')
        # Query latency
        duration_data = await cls.query_prometheus_instant('probe_duration_seconds{job="blackbox"}')
        
        # Query penunjang klasifikasi error
        dns_time_data = await cls.query_prometheus_instant('probe_dns_lookup_time_seconds{job="blackbox"}')
        connect_time_data = await cls.query_prometheus_instant('probe_connect_latency_seconds{job="blackbox"}')

        def extract_domain_id(metric_labels: Dict[str, Any]) -> Optional[str]:
            return metric_labels.get("domain_id")

        # Inisialisasi map data
        if success_data:
            for item in success_data:
                d_id = extract_domain_id(item["metric"])
                if d_id:
                    # Nilai value berupa array [timestamp, value_string]
                    metrics[d_id] = {
                        "probe_success": int(item["value"][1]) == 1,
                        "checked_at": float(item["value"][0]),
                        "status_code": 0,
                        "response_time_ms": 0.0,
                        "dns_lookup_success": True,
                        "connection_success": True
                    }

        if status_code_data:
            for item in status_code_data:
                d_id = extract_domain_id(item["metric"])
                if d_id and d_id in metrics:
                    metrics[d_id]["status_code"] = int(item["value"][1])

        if duration_data:
            for item in duration_data:
                d_id = extract_domain_id(item["metric"])
                if d_id and d_id in metrics:
                    metrics[d_id]["response_time_ms"] = float(item["value"][1]) * 1000.0  # Konversi ke ms

        if dns_time_data:
            for item in dns_time_data:
                d_id = extract_domain_id(item["metric"])
                if d_id and d_id in metrics:
                    # Jika dns lookup time adalah 0 / NaN / atau tidak terukur saat down
                    val = item["value"][1]
                    # Di Prometheus, NaN dikirim sebagai string "NaN" atau "NaN"
                    if val == "NaN" or val == "0" and not metrics[d_id]["probe_success"]:
                        metrics[d_id]["dns_lookup_success"] = False

        if connect_time_data:
            for item in connect_time_data:
                d_id = extract_domain_id(item["metric"])
                if d_id and d_id in metrics:
                    val = item["value"][1]
                    if val == "NaN" and not metrics[d_id]["probe_success"]:
                        metrics[d_id]["connection_success"] = False

        return metrics
