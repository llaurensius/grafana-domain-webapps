import logging
import time
import httpx
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.repositories.incident_repo import IncidentRepository
from app.repositories.domain_repo import DomainRepository
from app.models.incident import Incident
from app.config import settings

logger = logging.getLogger("uvicorn.incident_service")

# Konstanta toleransi waktu (hindari magic number di dalam kode)
DOWNTIME_QUALIFY_SECONDS  = 295  # ~5 menit, buffer 5 detik untuk clock drift
RECOVERY_CONFIRM_SECONDS  = 180  # 3 menit — domain harus UP terus sebelum RESOLVED


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.domain_repo   = DomainRepository(db)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: Bulk HTTP Fetch dari Prometheus (Sinkronus)
    # ─────────────────────────────────────────────────────────────────────────
    def _fetch_all_metrics(self) -> dict | None:
        """
        Menarik semua metrik probe dalam satu sesi HTTP sinkronus.
        Dipanggil dari thread pool (scheduler def biasa), bukan event loop.
        """
        queries = {
            "success":     "probe_success",
            "ssl":         "probe_ssl_earliest_cert_expiry",
            "status_code": "probe_http_status_code",
            "dns":         "probe_dns_lookup_time_seconds",
        }
        results = {}
        try:
            with httpx.Client(timeout=10.0) as client:
                for key, promql in queries.items():
                    resp = client.get(
                        f"{settings.PROMETHEUS_URL}/api/v1/query",
                        params={"query": promql},
                    )
                    results[key] = (
                        resp.json().get("data", {}).get("result", [])
                        if resp.status_code == 200
                        else []
                    )
        except Exception as e:
            logger.error(f"[IncidentService] Gagal menghubungi Prometheus: {e}")
            return None
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE: Deterministik Error Classifier (In-Memory, O(1))
    # Tidak ada HTTP call per domain. Membaca dari dict yang sudah ada di memori.
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _classify_error(
        instance_url: str,
        dns_map:         dict,
        status_code_map: dict,
        ssl_map:         dict,
    ) -> str:
        """
        Mengklasifikasikan akar penyebab kegagalan berdasarkan snapshot metrik
        historis Prometheus — bukan probe ulang real-time.

        Urutan pemeriksaan penting (dari yang paling fundamental ke yang paling spesifik):
        1. DNS gagal → domain tidak bisa diresolvasi sama sekali.
        2. SSL kedaluwarsa → koneksi HTTPS ditolak oleh browser/klien.
        3. Status HTTP 0  → koneksi berhasil tapi tidak ada respons (timeout).
        4. HTTP 4xx/5xx   → server merespons tapi dengan kode error.
        """
        dns_time    = dns_map.get(instance_url, 0.0)
        status_code = status_code_map.get(instance_url, 0)
        ssl_expiry  = ssl_map.get(instance_url, 0.0)
        now_ts      = time.time()

        if dns_time == 0.0:
            return "DNS Lookup Failure"
        if ssl_expiry > 0 and ssl_expiry < now_ts:
            return "SSL Certificate Expired"
        if status_code == 0:
            return "Connection Refused / Timeout"
        if 400 <= status_code < 500:
            return f"HTTP 4xx Client Error (Code: {int(status_code)})"
        if status_code >= 500:
            return f"HTTP 5xx Server Error (Code: {int(status_code)})"
        return "Unknown Outage"

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Entry point — dipanggil oleh scheduler setiap 1 menit
    # ─────────────────────────────────────────────────────────────────────────
    def process_metrics(self):
        """
        Memproses seluruh metrik Prometheus dengan 3 lapisan optimasi:

        1. BULK FETCH    : Semua metrik ditarik dalam satu batch, bukan per-domain.
        2. IN-MEMORY MAP : Lookup O(1) dari dictionary; nol HTTP call tambahan.
        3. UNIT OF WORK  : Semua mutasi dikumpulkan, satu db.commit() di akhir.

        Logika Transisi Status (Flapping-Aware):
        ┌─────────────┬───────────────────────────────────────────────────────┐
        │ Status Awal │ Kondisi               → Status Baru                   │
        ├─────────────┼───────────────────────────────────────────────────────┤
        │ (none)      │ DOWN detected         → ACTIVE                        │
        │ ACTIVE      │ DOWN (terus)          → ACTIVE (upgrade qualifies)     │
        │ ACTIVE      │ UP detected           → RECOVERY_PENDING               │
        │ RECOVERY    │ UP >= 3 menit         → RESOLVED (konfirmasi pulih)    │
        │ RECOVERY    │ DOWN kembali          → ACTIVE (flapping!)             │
        └─────────────┴───────────────────────────────────────────────────────┘
        """
        # ── Tahap 1: Ambil semua metrik dalam satu batch ──────────────────────
        metrics = self._fetch_all_metrics()
        if metrics is None:
            logger.warning("[IncidentService] Prometheus tidak dijangkau. Lewati siklus ini.")
            return

        if not metrics.get("success"):
            logger.info("[IncidentService] Data Prometheus kosong (target belum ada?).")
            return

        # ── Tahap 2: Bangun lookup dictionary O(1) dari hasil bulk ────────────
        def build_map(metric_list: list, cast=float) -> dict:
            return {
                r["metric"].get("instance"): cast(r["value"][1])
                for r in metric_list
                if r.get("metric") and r.get("value")
            }

        dns_map         = build_map(metrics.get("dns", []))
        status_code_map = build_map(metrics.get("status_code", []), cast=int)
        ssl_map         = build_map(metrics.get("ssl", []))

        # ── Tahap 3: Ambil semua data domain & insiden terbuka dari DB ────────
        active_domains: dict = {d.url: d for d in self.domain_repo.get_active()}

        # Satu query bulk: ambil semua insiden ACTIVE + RECOVERY_PENDING sekaligus
        open_incidents: dict[int, Incident] = {
            inc.domain_id: inc
            for inc in self.incident_repo.get_all_open()
        }

        now = datetime.now(timezone.utc)

        # ── Tahap 4: Iterasi & mutasi — TANPA commit di dalam loop ────────────
        for result in metrics.get("success", []):
            metric_meta   = result.get("metric", {})
            instance_url  = metric_meta.get("instance")
            probe_success = int(result.get("value", [0, "0"])[1])

            domain = active_domains.get(instance_url)
            if not domain:
                continue  # Domain sudah dihapus dari DB, abaikan

            incident = open_incidents.get(domain.id)

            # ── Cabang: Domain DOWN ───────────────────────────────────────────
            if probe_success == 0:

                if not incident:
                    # Tidak ada insiden terbuka → buat baru
                    error_type = self._classify_error(
                        instance_url, dns_map, status_code_map, ssl_map
                    )
                    self.db.add(Incident(
                        domain_id=domain.id,
                        status="ACTIVE",
                        qualifies_as_downtime=False,
                        error_type=error_type,
                        start_time=now,
                    ))

                elif incident.status == "RECOVERY_PENDING":
                    # Domain kembali down di tengah masa pemulihan → flapping!
                    # Kembalikan ke ACTIVE dan hapus timestamp recovery
                    logger.warning(
                        f"[Flapping] Domain '{instance_url}' kembali DOWN saat RECOVERY_PENDING. "
                        f"Status dikembalikan ke ACTIVE."
                    )
                    incident.status             = "ACTIVE"
                    incident.recovery_started_at = None

                elif incident.status == "ACTIVE":
                    # Domain masih down, cek apakah sudah layak jadi "downtime resmi"
                    duration_s = int(
                        (now - incident.start_time.replace(tzinfo=timezone.utc))
                        .total_seconds()
                    )
                    if duration_s >= DOWNTIME_QUALIFY_SECONDS and not incident.qualifies_as_downtime:
                        incident.qualifies_as_downtime = True

            # ── Cabang: Domain UP ─────────────────────────────────────────────
            elif probe_success == 1:

                if not incident:
                    pass  # Domain memang sudah UP dan tidak ada insiden → skip

                elif incident.status == "ACTIVE":
                    # Domain baru saja pulih → masuk masa tunggu konfirmasi
                    logger.info(
                        f"[Recovery] Domain '{instance_url}' terdeteksi UP. "
                        f"Masuk status RECOVERY_PENDING selama {RECOVERY_CONFIRM_SECONDS}s."
                    )
                    incident.status              = "RECOVERY_PENDING"
                    incident.recovery_started_at = now

                elif incident.status == "RECOVERY_PENDING":
                    # Domain masih UP di masa konfirmasi, hitung sudah berapa lama
                    recovery_elapsed = int(
                        (now - incident.recovery_started_at.replace(tzinfo=timezone.utc))
                        .total_seconds()
                    )

                    if recovery_elapsed >= RECOVERY_CONFIRM_SECONDS:
                        # Konfirmasi pulih — ubah ke RESOLVED
                        total_duration_s = int(
                            (now - incident.start_time.replace(tzinfo=timezone.utc))
                            .total_seconds()
                        )
                        incident.end_time             = now
                        incident.duration_seconds     = total_duration_s
                        incident.status               = "RESOLVED"
                        incident.recovery_started_at  = None
                        incident.qualifies_as_downtime = (
                            incident.qualifies_as_downtime
                            or total_duration_s >= DOWNTIME_QUALIFY_SECONDS
                        )
                        logger.info(
                            f"[Resolved] Domain '{instance_url}' RESOLVED setelah "
                            f"{total_duration_s}s total downtime."
                        )
                    # Jika belum 180 detik, biarkan saja (tetap RECOVERY_PENDING)

        # ── Tahap 5: SATU KALI bulk commit untuk semua perubahan ─────────────
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"[IncidentService] Bulk commit gagal, rollback dilakukan: {e}")
