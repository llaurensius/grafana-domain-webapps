# Finalisasi Project: Kesiapan GitHub, Deployment, & LAN Access

Dokumen ini memuat rencana audit final dan langkah-langkah untuk merapikan *project* agar siap diluncurkan (diunggah ke GitHub) dan dipasang di perangkat maupun server lain secara mudah.

## Audit Masalah yang Perlu Dirapikan
1. **File Berantakan di Root**: Banyak script *python* sementara (`csv_generator.py`, `patch_indexes.py`, `test_api.py`) dan file raw data (`siap_import.csv`, `daftar_domain_mentah.txt`) yang berserakan. Ini harus dipindah agar *root* bersih.
2. **Absennya .gitignore**: Belum ada `.gitignore` resmi, yang berisiko membuat folder rahasia/berat seperti `node_modules`, `__pycache__`, `.env`, atau data volume Docker terunggah ke GitHub.
3. **Frontend API Hardcode**: Di `client.js`, API saat ini dikunci ke `localhost:8000`. Jika kita mengakses *frontend* melalui *smartphone* atau laptop lain (via IP seperti `192.168.1.10:3001`), *request* API akan gagal karena *browser smartphone* akan mencoba menembak `localhost` (HP itu sendiri).
4. **Dokumentasi Absen**: `README.md` belum merangkum keseluruhan cara pasang (*deployment*) di perangkat lain.

## Proposed Changes

### 1. Struktur Folder (Cleanup)
Kita akan membuat folder `scripts/` dan `docs/data/` untuk menyimpan arsip pekerjaan sebelumnya yang masih berguna tapi bukan bagian inti dari *source code* aplikasi.

#### [MODIFY] Direktori *Root*
- Memindahkan `csv_generator.py`, `patch_indexes.py`, `test_api.py`, `test_err.py` ke dalam folder `scripts/`.
- Memindahkan `daftar_domain_mentah.txt`, `siap_import.csv`, `domain_template.csv` ke dalam folder `docs/data/`.

### 2. Kesiapan GitHub
#### [NEW] [`.gitignore`](file:///d:/Kuliah/Repository/grafana-domain-webapps/.gitignore)
- Membuat `.gitignore` komprehensif untuk mengabaikan `.env`, direktori `__pycache__`, `node_modules`, folder `.venv`, dan lain-lain.

### 3. Kesiapan LAN Access & Deployment (Frontend)
Untuk memecahkan masalah IP yang dinamis pada LAN tanpa memaksa pengguna melakukan *rebuild image* Docker setiap kali IP berganti, kita akan membuat URL API dinamis berbasiskan *hostname* pengakses.

#### [MODIFY] [`frontend/src/api/client.js`](file:///d:/Kuliah/Repository/grafana-domain-webapps/frontend/src/api/client.js)
- Mengubah `const API_URL = 'http://localhost:8000/api';` menjadi:
  ```javascript
  const hostname = window.location.hostname;
  const API_URL = `http://${hostname}:8000/api`;
  ```
- Dengan ini, bila pengguna mengakses web lewat `http://192.168.1.10:3001`, React akan otomatis mencari API di `192.168.1.10:8000`. Jika di-*deploy* ke VPS dengan domain asli, akan otomatis mengarah ke domain asli tersebut (asumsi tanpa *reverse proxy* kompleks).

### 4. Dokumentasi Lengkap
#### [MODIFY] [`README.md`](file:///d:/Kuliah/Repository/grafana-domain-webapps/README.md)
- Ditulis ulang untuk audiens GitHub: fitur utama, arsitektur, pra-syarat (Docker), dan cara instalasi instan.

#### [NEW] [`DEPLOYMENT.md`](file:///d:/Kuliah/Repository/grafana-domain-webapps/DEPLOYMENT.md)
- Panduan terperinci terkait *network*, cara memaparkan *port* ke internet atau ke LAN rumah/kantor, cara reset seluruh kontainer, serta interaksi antar servis di Docker Compose.

---

## User Review Required
> [!IMPORTANT]
> **Pendekatan Hostname di Frontend**
> Pendekatan `window.location.hostname` adalah cara terbaik, ternyaman, dan *zero-config* untuk *self-hosted* MVP berbasis Docker Compose tanpa melibatkan *reverse-proxy* seperti Nginx di depan *node*. Jika Anda mengakses frontend melalui VPS dengan domain publik, Anda harus memastikan port `8000` juga dibuka di VPS tersebut, ATAU Anda nantinya dapat membungkus *backend* dan *frontend* di belakang satu Nginx. Untuk MVP saat ini, apakah pendekatan `hostname` ini disetujui?

Apakah Anda menyetujui rencana *cleanup* file dan perombakan dokumentasi akhir ini? Jika ya, silakan setujui agar saya dapat langsung mengeksekusi tahapan finalisasinya!
