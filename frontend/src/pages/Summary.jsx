import React, { useState, useEffect } from 'react';
import { Download, Filter } from 'lucide-react';
import client from '../api/client';
import StatCard from '../components/UI/StatCard';

const Summary = () => {
  const [period, setPeriod] = useState('daily');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, [period]);

  const fetchStats = async () => {
    try {
      const res = await client.get(`/summary/stats?period=${period}`);
      setStats(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExport = async () => {
    try {
      const res = await client.get('/summary/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'incidents.csv');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Summary & Reports</h1>
        <button onClick={handleExport} className="btn"><Download size={18} /> Export CSV</button>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Filter size={20} color="var(--text-secondary)" />
          <h3 style={{ margin: 0, flex: 1 }}>Filter Period</h3>
          <select 
            value={period} 
            onChange={(e) => setPeriod(e.target.value)}
            style={{ padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
          >
            <option value="daily">Daily (Last 24h)</option>
            <option value="weekly">Weekly (Last 7 Days)</option>
            <option value="monthly">Monthly (Last 30 Days)</option>
          </select>
        </div>
      </div>

      {stats && (
        <div className="stats-grid">
          <StatCard title={`Total Valid Incidents (${period})`} value={stats.total_incidents} type="danger" />
          <StatCard title={`Total Downtime Minutes (${period})`} value={stats.total_downtime_minutes} type="warning" />
        </div>
      )}
      
      <div className="card">
        <p style={{ color: 'var(--text-secondary)' }}>
          Note: Stats only include incidents that have been verified as actual downtime (duration &gt; 5 minutes). Transient errors are filtered out to maintain SLA accuracy.
        </p>
      </div>
    </div>
  );
};

export default Summary;
