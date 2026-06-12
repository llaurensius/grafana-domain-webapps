# Project Requirement Document (PRD)

## Judul Proyek
Sistem Monitoring Domain Berbasis Grafana, Prometheus Blackbox Exporter, dan Custom Web App untuk Rekap Downtime

## Ringkasan Proyek
Dokumen ini mendefinisikan kebutuhan untuk sistem monitoring domain yang menggunakan Prometheus dan Blackbox Exporter sebagai mesin observability utama, Grafana sebagai lapisan visualisasi, dan custom web app sebagai antarmuka operasional untuk login, manajemen domain, rekap downtime, klasifikasi error, serta ekspor data CSV.[cite:1][cite:4][cite:6]

Target sistem adalah memonitor lebih dari 100 domain, mendeteksi kondisi down yang berlangsung lebih dari 5 menit, menampilkan ringkasan performa harian, mingguan, dan bulanan, serta menyimpan histori kejadian ke database untuk analisis dan pelaporan.[cite:1][cite:6][cite:10]

## Latar Belakang
Grafana secara umum berperan sebagai dashboard dan visualisasi, sedangkan Prometheus bersama Blackbox Exporter lebih tepat dijadikan sumber data monitoring untuk probe HTTP dan pengumpulan metrik status endpoint.[cite:1][cite:4][cite:6]

Pendekatan ini cocok untuk kebutuhan operasional karena metrik seperti `probe_success` dapat menunjukkan keberhasilan probe, sedangkan `probe_http_status_code` dapat membantu mengidentifikasi HTTP status seperti 404, 500, atau kondisi gagal respons.[cite:3][cite:6]

Untuk kasus kegagalan sebelum respons HTTP diterima, status code dapat bernilai `0`, yang menandakan kegagalan koneksi atau error jaringan sebelum server memberikan respons aplikasi.[cite:9][cite:10]

## Tujuan Produk
Sistem ini dirancang untuk menyediakan satu solusi monitoring domain yang:

- Memantau 100+ domain secara terpusat.
- Mengizinkan tambah, ubah, dan hapus domain melalui UI.
- Menampilkan status domain online/offline secara near real-time di Grafana dan web app.[cite:1][cite:4]
- Mencatat downtime yang valid hanya jika durasinya melebihi 5 menit.
- Menyediakan rekap downtime harian, mingguan, dan bulanan.
- Menampilkan klasifikasi error HTTP dan error koneksi.
- Menyediakan login untuk single-user access.
- Mengekspor data kejadian dan ringkasan ke format CSV.

## Ruang Lingkup

### In Scope
- Setup lokal pada WSL sebagai environment awal pengembangan dan pengujian.
- Deployment komponen dengan Docker Compose.
- Prometheus sebagai time-series database monitoring.
- Blackbox Exporter sebagai probe engine HTTP/HTTPS endpoint.[cite:1][cite:4][cite:6]
- Grafana sebagai dashboard visualisasi status dan metrik.[cite:4]
- Custom web app dengan login.
- CRUD domain monitoring melalui antarmuka web.
- Integrasi web app ke Prometheus API sebagai sumber data utama.
- Penyimpanan histori event ke database aplikasi.
- Ringkasan downtime per hari, minggu, dan bulan.
- Deteksi error code dan pesan/kategori error.
- Export CSV dari tabel data monitoring dan rekap.

### Out of Scope
- Notifikasi ke Telegram, Email, atau WhatsApp.
- Multi-user role management selain single-user.
- Root cause analysis tingkat infrastruktur seperti packet capture, distributed tracing, atau APM.
- Auto-remediation saat domain down.
- Monitoring non-web protocol di fase awal, kecuali ditambahkan pada fase berikutnya.

## Pemangku Kepentingan
| Peran | Tanggung Jawab |
|---|---|
| Owner/User | Mengelola domain, melihat dashboard, menganalisis downtime, ekspor data |
| System Admin | Menyiapkan WSL, Docker, service container, backup, dan operasional awal |
| Application System | Mengambil data dari Prometheus, menyimpan histori, menampilkan rekap |
| Monitoring Stack | Melakukan probe endpoint dan menyediakan metrik status [cite:1][cite:4] |

## Asumsi Arsitektur
Arsitektur dasar sistem terdiri dari target domain, Blackbox Exporter untuk melakukan probe HTTP, Prometheus untuk scrape hasil probe, Grafana untuk visualisasi, custom web app untuk operasi bisnis, dan database aplikasi untuk histori event dan metadata domain.[cite:1][cite:4][cite:6]

Web app tidak menggunakan Grafana sebagai sumber data utama, melainkan mengambil data dari Prometheus API agar agregasi histori, ekspor, dan logika aplikasi tidak tergantung pada layer visualisasi.[cite:1][cite:4]

## Kebutuhan Fungsional

### 1. Autentikasi
- Sistem menyediakan halaman login.
- Hanya satu akun aktif yang diperlukan pada fase awal.
- User yang belum login tidak dapat mengakses dashboard internal.
- Session login harus memiliki timeout yang dapat dikonfigurasi.

### 2. Manajemen Domain
- User dapat menambah domain/URL target dari UI.
- User dapat mengubah target monitoring.
- User dapat menghapus target monitoring.
- User dapat mengaktifkan atau menonaktifkan target tanpa menghapus data historis.
- Setiap target minimal memiliki field: nama domain, URL, protocol, interval probe, status aktif, created_at, updated_at.

### 3. Monitoring Status
- Sistem menampilkan status online/offline untuk setiap domain.
- Sistem mengambil metrik dari Prometheus untuk menampilkan hasil probe terbaru.[cite:1][cite:6]
- Sistem menampilkan last check time, response status, response time, dan status availability.[cite:1][cite:4]
- Sistem harus dapat menangani lebih dari 100 target domain aktif.

### 4. Aturan Downtime
- Downtime hanya dianggap valid jika status gagal berlangsung lebih dari 5 menit.
- Gangguan di bawah 5 menit dicatat sebagai transient issue atau ignored incident.
- Sistem harus menggabungkan beberapa probe gagal berurutan menjadi satu incident jika masih dalam satu rentang gangguan.
- Incident berakhir saat probe kembali sukses.

### 5. Klasifikasi Error
- Sistem menampilkan status HTTP seperti 200, 301, 302, 404, 500, 502, 503 jika tersedia dari probe.[cite:3][cite:6]
- Sistem mengelompokkan error non-HTTP, misalnya timeout, DNS failure, connection refused, connection reset, atau status code `0` sebagai failed-before-response.[cite:9][cite:10]
- Sistem menampilkan label error yang mudah dibaca seperti Bad Gateway, Not Found, Internal Server Error, Connection Error, Timeout, dan DNS Error.

### 6. Ringkasan dan Rekap
- Sistem menyediakan ringkasan downtime harian.
- Sistem menyediakan ringkasan downtime mingguan.
- Sistem menyediakan ringkasan downtime bulanan.
- Ringkasan minimal mencakup jumlah incident, total downtime, top affected domains, dan distribusi error.
- Tabel rekap mendukung filter berdasarkan tanggal, domain, status, dan kategori error.

### 7. Dashboard Web App
- Web app menampilkan KPI utama: total domain, domain up, domain down, incident aktif, downtime hari ini.
- Web app menampilkan tabel status domain terkini.
- Web app menampilkan histori incident.
- Web app menampilkan panel ringkasan periodik.
- Web app menyediakan tombol export CSV untuk data yang difilter.

### 8. Dashboard Grafana
- Grafana menampilkan panel status domain.
- Grafana menampilkan tren availability dan response metrics dari Blackbox Exporter.[cite:1][cite:4]
- Grafana digunakan sebagai observability dashboard, bukan antarmuka CRUD domain.

### 9. Export Data
- User dapat mengekspor tabel incident ke file CSV.
- User dapat mengekspor ringkasan harian, mingguan, dan bulanan ke CSV.
- Export mengikuti filter yang sedang aktif di UI.

### 10. Audit dan Logging
- Sistem mencatat aktivitas login.
- Sistem mencatat perubahan CRUD domain.
- Sistem mencatat job sinkronisasi data dari Prometheus.
- Sistem mencatat error internal aplikasi.

## Kebutuhan Non-Fungsional

### Kinerja
- Dashboard utama sebaiknya termuat dalam kurang dari 3 detik untuk dataset normal lokal.
- Query tabel utama sebaiknya merespons dalam kurang dari 2 detik pada rentang data operasional umum.
- Sistem harus tetap usable untuk 100+ domain aktif.

### Reliabilitas
- Jika Prometheus tidak merespons, web app harus menampilkan status gangguan integrasi, bukan salah menganggap semua domain down.[cite:2][cite:8]
- Sistem harus membedakan antara target website down dan datasource/no-data problem.[cite:2][cite:8]
- Job sinkronisasi harus idempotent untuk mencegah duplikasi incident.

### Keamanan
- Password disimpan dalam bentuk hash.
- Session harus aman dan memiliki mekanisme logout.
- Endpoint admin harus memerlukan autentikasi.
- Secret dan credential disimpan melalui environment variable.

### Maintainability
- Sistem dibangun modular agar monitoring stack dan web app dapat dikembangkan terpisah.
- Konfigurasi target dan service sebaiknya terdokumentasi.
- Struktur project harus mendukung deployment ulang dari nol.

## Model Data Tingkat Tinggi

### Entitas Domain
- id
- name
- target_url
- protocol
- probe_interval
- active
- created_at
- updated_at

### Entitas Probe Snapshot
- id
- domain_id
- checked_at
- probe_success
- http_status_code
- response_time_ms
- error_category
- error_message
- source_metric_ref

### Entitas Incident
- id
- domain_id
- start_time
- end_time
- duration_seconds
- qualifies_as_downtime
- root_error_category
- root_error_message
- incident_status

### Entitas User
- id
- username
- password_hash
- last_login_at

### Entitas Audit Log
- id
- user_id
- action_type
- action_detail
- created_at

## Alur Sistem
1. User menambahkan domain melalui web app.
2. Target domain didaftarkan ke konfigurasi monitoring.
3. Blackbox Exporter melakukan probe HTTP/HTTPS pada target.[cite:1][cite:6]
4. Prometheus melakukan scrape hasil probe secara berkala.[cite:1][cite:4]
5. Grafana membaca metrik untuk dashboard visualisasi.[cite:4]
6. Web app membaca data metrik dari Prometheus API dan menyimpan snapshot/incident ke database aplikasi.[cite:1]
7. Web app menghitung incident valid berdasarkan threshold >5 menit.
8. User melihat status, histori, dan mengekspor laporan CSV dari dashboard.

## User Stories
- Sebagai user, ingin login ke sistem agar hanya pengguna sah yang dapat melihat dashboard.
- Sebagai user, ingin menambah domain baru agar domain langsung ikut dimonitor.
- Sebagai user, ingin melihat status domain terkini agar cepat mengetahui website mana yang down.
- Sebagai user, ingin melihat error HTTP atau error koneksi agar dapat memahami jenis gangguan.
- Sebagai user, ingin melihat total downtime harian, mingguan, dan bulanan agar bisa mengevaluasi kestabilan layanan.
- Sebagai user, ingin mengekspor CSV agar data bisa dianalisis lebih lanjut.

## Acceptance Criteria Utama
| Fitur | Acceptance Criteria |
|---|---|
| Login | User dapat login dengan kredensial valid dan gagal masuk jika kredensial salah |
| CRUD domain | Domain dapat ditambah, diubah, dinonaktifkan, dan dihapus dari UI |
| Monitoring | Status domain terbaru muncul di web app dan cocok dengan metrik Prometheus [cite:1][cite:6] |
| Downtime threshold | Incident hanya dihitung sebagai downtime jika berlangsung lebih dari 5 menit |
| Error classification | Sistem menampilkan HTTP error dan kategori connection error yang dapat dibaca [cite:6][cite:10] |
| Summary | Sistem menghasilkan ringkasan harian, mingguan, dan bulanan |
| CSV export | Data tabel dan summary dapat diekspor ke CSV |
| Data source failure handling | Gangguan Prometheus/no-data tidak ditampilkan sebagai website down massal [cite:2][cite:8] |

## Risiko dan Mitigasi
| Risiko | Dampak | Mitigasi |
|---|---|---|
| Konfigurasi Prometheus/Blackbox salah | Data monitoring tidak akurat | Sediakan template config dan health check stack |
| Status code 0 membingungkan | Salah interpretasi error | Mapping ke kategori connection/pre-response failure [cite:9][cite:10] |
| Datasource no-data dianggap downtime | False positive besar | Pisahkan status integrasi vs status target [cite:2][cite:8] |
| Jumlah domain meningkat | Query melambat | Gunakan indexing DB, pagination, dan agregasi terjadwal |
| Deploy ulang dari nol | Setup memakan waktu | Gunakan Docker Compose dan dokumentasi bootstrap |

## Rekomendasi Teknologi
| Layer | Rekomendasi |
|---|---|
| Monitoring engine | Prometheus + Blackbox Exporter [cite:1][cite:4][cite:6] |
| Visualization | Grafana [cite:4] |
| App backend | Python FastAPI atau Node.js Express/NestJS |
| App frontend | React/Next.js atau server-rendered dashboard ringan |
| Database | PostgreSQL lebih disarankan; SQLite dapat dipakai untuk prototipe |
| Deployment | Docker Compose di WSL |
| Reverse proxy | Nginx atau Traefik |

## MVP yang Disarankan
Fase MVP sebaiknya mencakup login, CRUD domain, integrasi Prometheus API, tabel status domain, incident tracking dengan threshold >5 menit, klasifikasi error dasar, ringkasan harian/mingguan/bulanan, dan export CSV.

Grafana dashboard, database historis, dan web app reporting sudah cukup untuk menghasilkan sistem monitoring operasional yang usable pada tahap awal.[cite:1][cite:4]

## Fase Lanjutan
- Penambahan filter lanjutan dan pencarian cepat.
- Dukungan pause/maintenance window per domain.
- Dukungan tagging domain per kategori atau environment.
- Dukungan SLA report.
- Dukungan multi-user role bila diperlukan ke depan.
- Dukungan alert browser real-time atau in-app notification center.

## Pertanyaan Teknis Lanjutan untuk Tahap Desain
- Apakah penambahan domain dari UI akan otomatis memperbarui file konfigurasi Prometheus/Blackbox, atau melalui registry/servicediscovery tersendiri?
- Berapa interval probe yang diinginkan, misalnya 30 detik atau 1 menit?
- Apakah histori snapshot mentah disimpan penuh, atau hanya incident dan agregasi periodik?
- Apakah domain yang redirect dianggap sehat jika hasil akhir 200, atau redirect tertentu dianggap warning?
- Apakah sertifikat TLS expiry juga ingin dimasukkan ke fase berikutnya?

## Definisi Sukses
Proyek dianggap berhasil jika user dapat menjalankan stack monitoring dari nol di WSL, memonitor 100+ domain, melihat status aktual di Grafana dan web app, mendapatkan pencatatan downtime valid di atas 5 menit, memahami kategori error yang terjadi, serta mengekspor rekap operasional ke CSV tanpa bergantung pada proses manual.[cite:1][cite:4][cite:6]
