import axios from 'axios';

// Konfigurasi koneksi ke Backend FastAPI
// Pendekatan MVP: Menggunakan dynamic hostname agar bisa diakses di LAN (device lain)
// Pendekatan Production: Bisa di-override dengan VITE_API_URL (misal: '/api') jika memakai Reverse Proxy
const API_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000/api`;

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor untuk menyisipkan JWT token ke setiap request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
