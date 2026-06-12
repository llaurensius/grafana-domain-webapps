import React, { useState, useEffect } from 'react';
import { Activity, Globe, AlertTriangle } from 'lucide-react';
import StatCard from '../components/UI/StatCard';
import client from '../api/client';
import Badge from '../components/UI/Badge';

const Dashboard = () => {
  const [stats, setStats] = useState({ domains: 0, incidents: 0, downtime: 0 });
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [health, setHealth] = useState({ prometheus_connection: 'UP', prometheus_has_data: true });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Parallel requests for dashboard data
      const [domRes, incRes, sumRes, healthRes] = await Promise.all([
        client.get('/domains/'),
        client.get('/incidents/'),
        client.get('/summary/stats?period=daily'),
        client.get('/health/')
      ]);

      setStats({
        domains: domRes.data.length,
        incidents: sumRes.data.total_incidents,
        downtime: sumRes.data.total_downtime_minutes
      });
      
      setRecentIncidents(incRes.data.slice(0, 5)); // top 5 recent
      setHealth(healthRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      {health.prometheus_connection === 'DOWN' && (
        <div style={{ background: '#fee2e2', color: '#991b1b', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={20} />
          <strong>Warning:</strong> Backend cannot connect to Prometheus. Incident processing is paused.
        </div>
      )}
      {health.prometheus_connection === 'UP' && !health.prometheus_has_data && stats.domains > 0 && (
        <div style={{ background: '#fef3c7', color: '#92400e', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={20} />
          <strong>Warning:</strong> Prometheus is UP but returning no data. Check Blackbox exporter or Wait for targets to be scraped.
        </div>
      )}

      <div className="page-header">
        <h1>Dashboard Overview</h1>
      </div>

      <div className="stats-grid">
        <StatCard title="Total Domains" value={stats.domains} icon={<Globe size={24} />} />
        <StatCard title="24h Incidents" value={stats.incidents} icon={<AlertTriangle size={24} />} type={stats.incidents > 0 ? 'danger' : 'primary'} />
        <StatCard title="24h Downtime (Min)" value={stats.downtime} icon={<Activity size={24} />} type={stats.downtime > 0 ? 'danger' : 'success'} />
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Recent Incidents</h3>
        <table className="table-container">
          <thead>
            <tr>
              <th>Domain ID</th>
              <th>Start Time</th>
              <th>Status</th>
              <th>Downtime Confirmed</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {recentIncidents.length === 0 ? (
              <tr><td colSpan="5" style={{ textAlign: 'center' }}>No recent incidents. All systems operational.</td></tr>
            ) : (
              recentIncidents.map(inc => (
                <tr key={inc.id}>
                  <td>{inc.domain_id}</td>
                  <td>{new Date(inc.start_time).toLocaleString()}</td>
                  <td>
                    <Badge type={inc.status === 'ACTIVE' ? 'danger' : 'success'}>{inc.status}</Badge>
                  </td>
                  <td>
                    {inc.qualifies_as_downtime ? <Badge type="danger">Yes (> 5m)</Badge> : <Badge type="warning">No</Badge>}
                  </td>
                  <td>{inc.error_type || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
