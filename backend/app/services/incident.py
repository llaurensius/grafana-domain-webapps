import datetime
import logging
from sqlalchemy.orm import Session
from app.repositories.incident import IncidentRepository
from app.repositories.domain import DomainRepository
from app.models.incident import Incident
from app.services.prometheus import PrometheusService

logger = logging.getLogger("domain_monitor.incident_service")

class IncidentService:
    @staticmethod
    def classify_error(
        status_code: int,
        dns_lookup_success: bool,
        connection_success: bool,
        response_time_ms: float,
        probe_success: bool
    ) -> tuple[str, str]:
        """
        Klasifikasi error berdasarkan metrik Prometheus/Blackbox Exporter.
        Mengembalikan (error_category, error_message).
        """
        if probe_success:
            return "None", "Website berjalan normal."
            
        if not dns_lookup_success:
            return "DNS Error", "Gagal menyelesaikan nama host domain (DNS lookup failed)."
            
        if not connection_success:
            return "Connection Error", "Gagal membangun koneksi TCP / Connection refused."

        if status_code == 404:
            return "Not Found", "Halaman target tidak ditemukan (HTTP 404)."
            
        if status_code == 502:
            return "Bad Gateway", "Gateway/Proxy menerima respons tidak valid dari upstream (HTTP 502)."
            
        if status_code >= 400 and status_code < 500:
            return f"HTTP 4xx", f"Client error dengan status HTTP {status_code}."
            
        if status_code >= 500 and status_code < 600:
            return f"HTTP 5xx", f"Server error dengan status HTTP {status_code}."
            
        # Jika response time mendekati 10 detik (timeout Blackbox)
        if response_time_ms >= 9500:
            return "Timeout", "Koneksi dibatalkan karena melebihi batas waktu respons (timeout 10s)."
            
        if status_code == 0:
            return "status code 0 / failed before response", "Kegagalan koneksi sebelum menerima HTTP respons (SSL/TLS handshake error atau connection reset)."
            
        return "Unknown Error", f"Gangguan tidak dikenal. Status Code: {status_code}."

    @classmethod
    async def process_domain_status_sync(cls, db: Session) -> dict:
        """
        Melakukan sinkronisasi status domain dari Prometheus.
        Dipanggil oleh background worker secara periodik (setiap 1 menit).
        """
        result_summary = {
            "processed": 0,
            "created_incidents": 0,
            "resolved_incidents": 0,
            "status": "success",
            "message": ""
        }

        # 1. Cek kesehatan Prometheus datasource
        prom_health = await PrometheusService.check_prometheus_health()
        if prom_health == "offline":
            msg = "Gagal sinkronisasi: Integrasi Prometheus OFFLINE. Data source bermasalah."
            logger.error(msg)
            result_summary["status"] = "failed"
            result_summary["message"] = msg
            return result_summary
            
        # 2. Ambil metrik terkini
        latest_metrics = await PrometheusService.get_latest_metrics()
        if not latest_metrics:
            msg = "Gagal sinkronisasi: Tidak ada data metrik dari Prometheus (no_data)."
            logger.warning(msg)
            result_summary["status"] = "no_data"
            result_summary["message"] = msg
            return result_summary

        domain_repo = DomainRepository(db)
        incident_repo = IncidentRepository(db)

        # 3. Ambil semua domain aktif dari DB
        active_domains = domain_repo.get_all(active_only=True)
        now = datetime.datetime.utcnow()

        for domain in active_domains:
            domain_id_str = str(domain.id)
            result_summary["processed"] += 1

            # Cari metrik untuk domain ini
            metric = latest_metrics.get(domain_id_str)
            if not metric:
                logger.warning(f"No metric found for domain: {domain.name} (ID: {domain.id})")
                continue

            probe_success = metric["probe_success"]
            status_code = metric["status_code"]
            response_time_ms = metric["response_time_ms"]
            dns_success = metric["dns_lookup_success"]
            conn_success = metric["connection_success"]

            # Cari incident ACTIVE
            active_incident = incident_repo.get_active_by_domain(domain.id)

            if not probe_success:
                # Target DOWN
                if not active_incident:
                    # Classify error
                    err_cat, err_msg = cls.classify_error(
                        status_code, dns_success, conn_success, response_time_ms, probe_success
                    )
                    # Buat incident baru
                    incident_repo.create(domain.id, err_cat, err_msg)
                    result_summary["created_incidents"] += 1
                    logger.info(f"Downtime terdeteksi untuk domain: {domain.name} ({domain.target_url}). Insiden baru dibuat.")
                else:
                    # Sudah ada incident ACTIVE, cek durasinya untuk kualifikasi downtime > 5 menit (300 detik)
                    duration = (now - active_incident.start_time).total_seconds()
                    if duration > 300 and not active_incident.qualifies_as_downtime:
                        incident_repo.update_qualify_status(active_incident, True)
                        logger.info(f"Downtime untuk domain: {domain.name} dikualifikasi sebagai insiden downtime valid (> 5 menit).")
            else:
                # Target UP
                if active_incident:
                    # Selesaikan incident
                    duration_seconds = int((now - active_incident.start_time).total_seconds())
                    qualifies = duration_seconds > 300
                    
                    incident_repo.resolve(active_incident, now, qualifies)
                    result_summary["resolved_incidents"] += 1
                    logger.info(f"Domain: {domain.name} kembali UP. Insiden selesai. Durasi: {duration_seconds} detik. Downtime valid: {qualifies}")

        return result_summary
