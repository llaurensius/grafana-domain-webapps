import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Activity, Globe, AlertCircle, BarChart2, Download, LogOut, Trash2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import client from '../api/client';

const Layout = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleWipeDatabase = async () => {
    if (window.confirm("WARNING: Are you absolutely sure you want to WIPE the entire database? This action cannot be undone and will delete ALL domains and incidents!")) {
      try {
        await client.delete('/domains/wipe-all');
        alert('Database has been wiped completely.');
        window.location.reload();
      } catch (err) {
        alert('Failed to wipe database: ' + (err.response?.data?.detail || err.message));
      }
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <h2>DomMon</h2>
        <ul className="sidebar-menu">
          <li>
            <NavLink to="/" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"} end>
              <Activity size={20} /> Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink to="/domains" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"}>
              <Globe size={20} /> Domains
            </NavLink>
          </li>
          <li>
            <NavLink to="/incidents" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"}>
              <AlertCircle size={20} /> Incidents
            </NavLink>
          </li>
          <li>
            <NavLink to="/summary" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"}>
              <BarChart2 size={20} /> Summary
            </NavLink>
          </li>
          <li>
            <NavLink to="/reports" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"}>
              <Download size={20} /> Reports
            </NavLink>
          </li>
        </ul>
        <button onClick={handleWipeDatabase} className="btn outline" style={{ marginTop: 'auto', width: '100%', justifyContent: 'center', borderColor: 'var(--danger-color)', color: 'var(--danger-color)', marginBottom: '0.5rem' }}>
          <Trash2 size={18} /> Wipe Database
        </button>
        <button onClick={handleLogout} className="btn outline" style={{ width: '100%', justifyContent: 'center' }}>
          <LogOut size={18} /> Logout
        </button>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
