from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func, expression
from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id                    = Column(Integer, primary_key=True, index=True)
    domain_id             = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    start_time            = Column(DateTime(timezone=True), default=func.now(), index=True)
    end_time              = Column(DateTime(timezone=True), nullable=True)
    duration_seconds      = Column(Integer, nullable=True)
    qualifies_as_downtime = Column(Boolean, default=False, index=True)
    error_type            = Column(String, nullable=True)

    # ── Status diperluas untuk mendukung Flapping Detection ──────────────────
    # ACTIVE          : Domain sedang down, insiden terbuka.
    # RECOVERY_PENDING: Domain terdeteksi UP, tapi masih dalam masa tunggu
    #                   konfirmasi (3 menit). Belum dianggap pulih.
    # RESOLVED        : Domain dikonfirmasi UP selama >= 3 menit berturut-turut.
    status = Column(String, default="ACTIVE", index=True)

    # Timestamp saat status berubah ke RECOVERY_PENDING.
    # Digunakan untuk menghitung apakah 180 detik masa tunggu sudah terlampaui.
    recovery_started_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # ── Partial Unique Index (Idempotency Guard di level Database) ────────
        # Memastikan hanya ada SATU baris dengan status 'ACTIVE' atau
        # 'RECOVERY_PENDING' per domain_id.
        # PostgreSQL akan menolak INSERT duplikat dengan IntegrityError,
        # bahkan jika ada bug race condition di level aplikasi.
        #
        # Catatan: Indeks partial ini HANYA berlaku saat status adalah
        # 'ACTIVE' atau 'RECOVERY_PENDING'. Baris RESOLVED tidak dibatasi
        # (domain boleh punya banyak riwayat insiden yang sudah resolved).
        Index(
            "uix_one_open_incident_per_domain",
            "domain_id",
            unique=True,
            postgresql_where=(
                expression.or_(
                    expression.column("status") == "ACTIVE",
                    expression.column("status") == "RECOVERY_PENDING",
                )
            ),
        ),
    )
