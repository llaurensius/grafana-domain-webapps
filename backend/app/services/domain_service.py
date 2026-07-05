"""
domain_service.py
-----------------
Bertanggung jawab atas seluruh logika bisnis yang berkaitan dengan domain, meliputi:
  1. Operasi CRUD domain (buat, perbarui, hapus, dll.) via DomainRepository.
  2. Pemrosesan metrik Prometheus (status probe, SSL, kode HTTP, DNS).
  3. Kalkulasi info SSL (hari kedaluwarsa) dan pemetaan kode error jaringan.
  4. Sinkronisasi target ke file Prometheus.

Prinsip: Router hanya menerima request HTTP dan mengembalikan response.
         Semua logika bisnis ada di sini.
"""

import time
from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.domain_repo import DomainRepository
from app.schemas.domain import DomainCreate, DomainUpdate, DomainResponse
from app.services.prometheus_service import PrometheusService
from app.models.incident import Incident


# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------

# Batas hari untuk memunculkan peringatan SSL
SSL_WARNING_THRESHOLD_DAYS = 14

# Pemetaan kode HTTP spesifik ke pesan ramah pengguna
HTTP_STATUS_MESSAGES: dict[int, str] = {
    404: "404 Page Not Found",
    403: "403 Forbidden",
    500: "500 Internal Server Error",
    502: "502 Bad Gateway",
    503: "503 Service Unavailable",
}


# ---------------------------------------------------------------------------
# Pure helper functions (fungsi murni, mudah diuji secara unit)
# ---------------------------------------------------------------------------

def _normalize_url(url: Optional[str]) -> str:
    """Menormalkan URL dengan menghapus trailing slash untuk konsistensi kunci lookup."""
    return url.rstrip("/") if url else ""


def _calculate_ssl_info(expiry_timestamp: float, current_time: float) -> str:
    """
    Menghitung dan mengembalikan string informasi SSL berdasarkan timestamp kedaluwarsa.

    Args:
        expiry_timestamp: Unix timestamp kedaluwarsa sertifikat SSL dari Prometheus.
        current_time:     Unix timestamp saat ini.

    Returns:
        String deskriptif: "Expired", "Warning: X days left", atau "Valid (X days)".
    """
    days_left = int((expiry_timestamp - current_time) / 86400)
    if days_left < 0:
        return "Expired"
    if days_left <= SSL_WARNING_THRESHOLD_DAYS:
        return f"Warning: {days_left} days left"
    return f"Valid ({days_left} days)"


def _classify_network_error(status_code: float, ip_hash: float) -> str:
    """
    Mengklasifikasikan penyebab kegagalan probe berdasarkan metrik Prometheus.

    Urutan pengecekan:
      1. ip_hash == 0  → DNS tidak dapat di-resolve (NXDOMAIN).
      2. status_code == 0 → Koneksi ditolak atau timeout.
      3. Kode HTTP spesifik (4xx/5xx) dari HTTP_STATUS_MESSAGES.
      4. Generik 4xx / 5xx jika tidak ada pemetaan spesifik.
      5. Fallback "Unknown Error".

    Args:
        status_code: Nilai probe_http_status_code dari Prometheus.
        ip_hash:     Nilai probe_ip_addr_hash dari Prometheus (0 = DNS gagal).

    Returns:
        String pesan error yang deskriptif.
    """
    if ip_hash == 0:
        return "DNS_PROBE_FINISHED_NXDOMAIN"
    if status_code == 0:
        return "ERR_CONNECTION_REFUSED"

    status_int = int(status_code)

    if status_int in HTTP_STATUS_MESSAGES:
        return HTTP_STATUS_MESSAGES[status_int]

    if 400 <= status_int < 500:
        return f"{status_int} Client Error"
    if status_int >= 500:
        return f"{status_int} Server Error"

    return "Unknown Error"


# ---------------------------------------------------------------------------
# Fungsi pembangun lookup map dari raw Prometheus data
# ---------------------------------------------------------------------------

def _build_probe_status_map(success_results: list) -> dict[str, int]:
    """Membangun map {normalized_url: probe_success (0/1)} dari hasil query Prometheus."""
    return {
        _normalize_url(r.get("metric", {}).get("instance")): int(r.get("value", [0, "0"])[1])
        for r in success_results
        if r.get("metric", {}).get("instance")
    }


def _build_ssl_info_map(ssl_results: list, current_time: float) -> dict[str, str]:
    """Membangun map {normalized_url: ssl_info_string} dari hasil query Prometheus."""
    ssl_map = {}
    for r in ssl_results:
        url_key = _normalize_url(r.get("metric", {}).get("instance"))
        if not url_key:
            continue
        try:
            expiry_ts = float(r.get("value", [0, "0"])[1])
            ssl_map[url_key] = _calculate_ssl_info(expiry_ts, current_time)
        except (ValueError, IndexError):
            ssl_map[url_key] = "Unknown"
    return ssl_map


def _build_error_info_map(
    probe_status_map: dict[str, int],
    status_code_results: list,
    ip_hash_results: list,
) -> dict[str, str]:
    """
    Membangun map {normalized_url: error_message} hanya untuk domain yang DOWN.
    Efisiensi memori: hanya memproses URL yang probe-nya gagal (probe_success == 0).
    """
    status_code_map: dict[str, float] = {
        _normalize_url(r.get("metric", {}).get("instance")): float(r.get("value", [0, "0"])[1])
        for r in status_code_results
        if r.get("metric", {}).get("instance")
    }
    ip_hash_map: dict[str, float] = {
        _normalize_url(r.get("metric", {}).get("instance")): float(r.get("value", [0, "0"])[1])
        for r in ip_hash_results
        if r.get("metric", {}).get("instance")
    }

    error_map: dict[str, str] = {}
    for url_key, success in probe_status_map.items():
        if success == 1:
            continue  # Domain UP, tidak perlu klasifikasi error
        status_code = status_code_map.get(url_key, 0)
        ip_hash = ip_hash_map.get(url_key, 0)
        error_map[url_key] = _classify_network_error(status_code, ip_hash)

    return error_map


# ---------------------------------------------------------------------------
# DomainService — Kelas utama yang di-inject ke router
# ---------------------------------------------------------------------------

class DomainService:
    """
    Service layer untuk operasi domain.

    Bertanggung jawab sebagai satu-satunya titik kontak antara router dan
    logika bisnis domain (CRUD, status enrichment, Prometheus sync).
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = DomainRepository(db)

    # ------------------------------------------------------------------
    # Operasi CRUD Domain
    # ------------------------------------------------------------------

    def create_domain(self, domain_in: DomainCreate):
        """Membuat domain baru dan langsung men-sinkronkan target Prometheus."""
        domain = self.repo.create(domain_in)
        self._sync_prometheus()
        return domain

    def update_domain(self, domain_id: int, domain_in: DomainUpdate):
        """
        Memperbarui domain. Mengembalikan None jika domain tidak ditemukan.
        Sinkronisasi Prometheus dilakukan setelah update berhasil.
        """
        domain = self.repo.get_by_id(domain_id)
        if not domain:
            return None
        updated = self.repo.update(domain, domain_in)
        self._sync_prometheus()
        return updated

    def delete_domain(self, domain_id: int):
        """
        Menghapus domain. Mengembalikan domain yang dihapus, atau None jika tidak ada.
        Sinkronisasi Prometheus dilakukan setelah hapus berhasil.
        """
        domain = self.repo.get_by_id(domain_id)
        if domain:
            self.repo.delete(domain)
            self._sync_prometheus()
        return domain

    def bulk_create_domains(self, domains_in: List[DomainCreate]):
        """Membuat banyak domain sekaligus. Sinkronisasi dilakukan sekali di akhir."""
        domains = self.repo.bulk_create(domains_in)
        self._sync_prometheus()
        return domains

    def bulk_delete_domains(self, domain_ids: List[int]):
        """Menghapus banyak domain sekaligus. Sinkronisasi dilakukan sekali di akhir."""
        self.repo.bulk_delete(domain_ids)
        self._sync_prometheus()

    # ------------------------------------------------------------------
    # Logika Utama: Enrichment Status Domain dengan Data Prometheus
    # ------------------------------------------------------------------

    async def get_domains_with_status(self) -> List[DomainResponse]:
        """
        Mengambil semua domain dan memperkayanya dengan data status real-time dari
        Prometheus (status UP/DOWN, info SSL, info error).

        Alur eksekusi:
          1. Ambil semua domain dari DB (1 query).
          2. Ambil metrik dari Prometheus (dengan cache 15 detik bawaan PrometheusService).
          3. Bangun lookup maps (probe_status, ssl_info, error_info) — masing-masing O(n).
          4. Ambil data incident aktif dari DB — 1 query, bukan N queries.
          5. Iterasi domain dan gabungkan semua data — O(n).

        Returns:
            List[DomainResponse] yang sudah diperkaya dengan status, ssl_info, error_info.
        """
        domains = self.repo.get_all()

        metrics = await PrometheusService.get_cached_metrics()

        probe_status_map: dict[str, int] = {}
        ssl_info_map: dict[str, str] = {}
        error_info_map: dict[str, str] = {}

        if metrics is not None:
            current_time = time.time()
            probe_status_map = _build_probe_status_map(metrics.get("success", []))
            ssl_info_map = _build_ssl_info_map(metrics.get("ssl", []), current_time)
            error_info_map = _build_error_info_map(
                probe_status_map,
                metrics.get("status_code", []),
                metrics.get("ip_hash", []),
            )

        active_incidents_map = self._get_active_incidents_map()

        return [
            self._enrich_domain(d, probe_status_map, ssl_info_map, error_info_map, active_incidents_map)
            for d in domains
        ]

    def _enrich_domain(
        self,
        domain,
        probe_status_map: dict[str, int],
        ssl_info_map: dict[str, str],
        error_info_map: dict[str, str],
        active_incidents_map: dict[int, object],
    ) -> DomainResponse:
        """
        Memperkaya satu objek domain dengan status, info SSL, dan info error.

        Status logic:
          - UNMONITORED : domain.is_active == False
          - PENDING     : domain aktif tetapi belum ada data dari Prometheus
          - UP          : probe_success == 1
          - DOWN        : probe_success == 0

        Error info untuk domain DOWN diutamakan dari incident aktif di DB (lebih akurat),
        kemudian fallback ke klasifikasi dari metrik Prometheus.
        """
        n_url = _normalize_url(domain.url)

        if not domain.is_active:
            return DomainResponse(
                id=domain.id,
                url=domain.url,
                name=domain.name,
                is_active=domain.is_active,
                created_at=domain.created_at,
                status="UNMONITORED",
                ssl_info="N/A",
                error_info=None,
            )

        if n_url not in probe_status_map:
            status = "PENDING"
        else:
            status = "UP" if probe_status_map[n_url] == 1 else "DOWN"

        ssl_info = (
            ssl_info_map.get(n_url, "N/A")
            if n_url.startswith("https")
            else "HTTP (No SSL)"
        )

        error_info: Optional[str] = None
        if status == "DOWN":
            inc = active_incidents_map.get(domain.id)
            error_info = (inc.error_type if inc and inc.error_type else None) or error_info_map.get(n_url)

        return DomainResponse(
            id=domain.id,
            url=domain.url,
            name=domain.name,
            is_active=domain.is_active,
            created_at=domain.created_at,
            status=status,
            ssl_info=ssl_info,
            error_info=error_info,
        )

    # ------------------------------------------------------------------
    # Metode Privat (Internal Helpers)
    # ------------------------------------------------------------------

    def _sync_prometheus(self) -> None:
        """Mengambil URL domain aktif dan menulis ulang file target Prometheus."""
        active_urls = [d.url for d in self.repo.get_active()]
        PrometheusService.sync_targets_file(active_urls)

    def _get_active_incidents_map(self) -> dict[int, object]:
        """
        Mengambil semua incident aktif dari DB dalam SATU query dan
        mengembalikannya sebagai dict {domain_id: incident} untuk lookup O(1).
        Menghindari N+1 query problem.
        """
        active_incidents = (
            self.db.query(Incident)
            .filter(Incident.status == "ACTIVE")
            .all()
        )
        return {inc.domain_id: inc for inc in active_incidents}

