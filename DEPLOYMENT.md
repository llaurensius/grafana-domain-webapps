# Deployment & Network Guide

This document explains the network architecture of the DomMon project and how to deploy it in different scenarios.

## Frontend to Backend Connectivity

A common issue in containerized web apps is connecting the browser (Frontend) to the API (Backend). We support two paradigms:

### 1. Dynamic Hostname (Local & LAN Access - Default MVP)
In `frontend/src/api/client.js`, the API URL is defined as:
```javascript
const API_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000/api`;
```

**How it works:**
- If you access `http://localhost:3001`, the API calls go to `http://localhost:8000`.
- If you access `http://192.168.1.10:3001` from a phone, the API calls go to `http://192.168.1.10:8000`.

**Trade-offs:**
- **Pros**: Zero configuration. Works out of the box for any device in the same network. No rebuild required if the server's IP changes.
- **Cons**: Both port `3001` and `8000` must be exposed and accessible on the host machine firewall. Not suitable for standard HTTPS production servers.

---

### 2. Reverse Proxy (Production VPS)
For a proper production deployment on a VPS (e.g., DigitalOcean, AWS EC2) with a real domain name (e.g., `https://monitor.yourdomain.com`), exposing multiple ports is a bad practice.

**The Reverse Proxy Approach:**
You should place an **Nginx** or **Traefik** proxy in front of the application. 

1. **Routing Strategy**:
   - Traffic to `https://monitor.yourdomain.com/` routes to the Frontend container (`port 80` inside container).
   - Traffic to `https://monitor.yourdomain.com/api/` routes to the Backend container (`port 8000` inside container).

2. **Frontend Configuration**:
   When building or running the frontend for production, set the environment variable:
   ```bash
   VITE_API_URL=/api
   ```
   This overrides the dynamic hostname and forces the frontend to use a **Relative API Path**. Now, regardless of the domain, the browser will append `/api` to the current origin, letting the Reverse Proxy route it securely to the backend.

**Trade-offs:**
- **Pros**: Secure, allows SSL/HTTPS termination, single port (443) exposure, hides backend architecture.
- **Cons**: Requires additional Nginx configuration and managing SSL certificates (Let's Encrypt).

---

## Deploying to a VPS (Step-by-Step)

If you are moving this project to a Cloud Linux VPS:

1. SSH into your VPS.
2. Install `docker` and `docker-compose-plugin`.
3. Clone the repository.
4. `cp .env.example .env` and **CHANGE** the default database passwords!
5. Optional: Install Nginx on the host machine to act as a Reverse Proxy.
6. Run `docker compose up -d --build`.
7. Setup `UFW` (Uncomplicated Firewall) to allow only necessary ports (22, 80, 443). Do not expose 8000 publicly if using Nginx.
