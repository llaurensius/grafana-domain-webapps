# Grafana Domain Monitoring WebApps (DomMon)

DomMon is an all-in-one monitoring system designed to track domain uptime, SSL expiration, and HTTP status codes using Prometheus & Blackbox Exporter, paired with a FastAPI backend and a React frontend for easy management.

## 🚀 Features
- **Dashboard & Summary**: Real-time overview of monitored domains, UP/DOWN status, and DNS/SSL metrics.
- **Incident Tracking**: Automatically tracks and stores historical downtime incidents, calculates duration, and categorizes errors.
- **Aggregated Reports**: Generate Executive Summary reports (Daily, Weekly, Monthly) per domain and export to Excel (.xlsx) or CSV.
- **Bulk Domain Management**: Import massive domain lists via CSV/Excel and manage them from a user-friendly UI.
- **Docker-Ready**: Packaged with Docker Compose for immediate deployment on local machines, LAN, or VPS.

## 🏗️ Architecture & Tech Stack
- **Frontend**: React.js (Vite), Lucide Icons, Axios.
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL), Pandas (Data Export).
- **Monitoring Engine**: Prometheus (Time-series data) & Blackbox Exporter (Active probing).
- **Visualization (Optional)**: Grafana.
- **Infrastructure**: Docker & Docker Compose.

## 📁 Folder Structure
```text
grafana-domain-webapps/
├── backend/            # FastAPI application
├── frontend/           # React application
├── monitoring/         # Prometheus, Grafana, Blackbox Configs
│   ├── prometheus/     # targets/websites.yml lives here
│   ├── blackbox/
│   └── grafana/
├── scripts/            # Helper scripts (DB operations, tests)
├── docs/               # Documentations and dummy data
├── docker-compose.yml  # Root deployment configuration
└── .env.example        # Environment variables template
```

## 🛠️ Quick Start (Installation)

### Prerequisites
- Docker and Docker Compose installed.

### 1. Clone Repository
```bash
git clone https://github.com/your-username/grafana-domain-webapps.git
cd grafana-domain-webapps
```

### 2. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
*(Leave default values for local/LAN MVP. Change passwords for Production VPS).*

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```

### 4. Access the Services
Once running, you can access the services at:
- **Frontend (UI)**: `http://localhost:3001`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Grafana**: `http://localhost:3000` (Default: admin / admin123)
- **Prometheus**: `http://localhost:9090`

## 📱 LAN Access & Multi-Device
By default, the React frontend is configured with a **Dynamic Hostname MVP Approach**. This means if you run this on a PC with IP `192.168.1.10`, you can grab your phone connected to the same WiFi and browse to:
👉 `http://192.168.1.10:3001`

The frontend will *automatically* detect the IP and correctly route API requests to `http://192.168.1.10:8000/api`. You do **not** need to hardcode IPs!

*(For Reverse Proxy or Production deployment, see `DEPLOYMENT.md`)*

## 🛑 Operations
- **Stop services**: `docker compose down`
- **Wipe Database & Reset**: Click the red "Wipe Database" button inside the UI sidebar (Warning: irreversible!).

## 💡 Troubleshooting
- **Frontend is blank or doesn't update**: The Vite dev server in Docker might cache the state. Run `docker restart monitoring-frontend`.
- **Target domains not showing in Prometheus**: Ensure the backend has permissions to write to `./monitoring/prometheus/targets/websites.yml`.
- **Database Connection Error**: Wait a few seconds for PostgreSQL to become fully healthy, then restart the backend: `docker restart monitoring-backend`.

## 🗺️ Roadmap
- Add authentication (JWT Login) to the frontend interface.
- Add alerting integrations (Telegram / Slack).
- Migrate from `npm run dev` to a production Nginx build for the frontend container.
