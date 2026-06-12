import React from 'react';
import { AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import Badge from './UI/Badge';

const IncidentTable = ({ incidents }) => {
  const tableContainerStyle = {
    width: '100%',
    overflowX: 'auto',
    backgroundColor: '#131520',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.08)'
  };

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'left',
    fontSize: '0.9rem'
  };

  const thStyle = {
    padding: '1rem 1.25rem',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    color: '#9ca3af',
    fontWeight: '600'
  };

  const tdStyle = {
    padding: '1rem 1.25rem',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    color: '#f3f4f6',
    verticalAlign: 'middle'
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDuration = (seconds) => {
    if (seconds === null || seconds === undefined) return 'Sedang Berlangsung';
    
    if (seconds < 60) {
      return `${seconds} detik`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes < 60) {
      return `${minutes} menit ${remainingSeconds} detik`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    return `${hours} jam ${remainingMinutes} menit ${remainingSeconds} detik`;
  };

  return (
    <div style={tableContainerStyle}>
      {incidents.length === 0 ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#9ca3af' }}>
          Tidak ada insiden tercatat untuk filter ini.
        </div>
      ) : (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Domain</th>
              <th style={thStyle}>Waktu Mulai (WIB)</th>
              <th style={thStyle}>Waktu Selesai (WIB)</th>
              <th style={thStyle}>Durasi Gangguan</th>
              <th style={thStyle}>Tipe Downtime</th>
              <th style={thStyle}>Kategori Error</th>
              <th style={thStyle}>Pesan Error</th>
              <th style={thStyle}>Status</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr 
                key={incident.id}
                style={{ transition: 'background-color 0.2s' }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.01)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <td style={tdStyle}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                    <span style={{ fontWeight: '600' }}>{incident.domain_name}</span>
                    <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{incident.domain_url}</span>
                  </div>
                </td>
                <td style={tdStyle}>{formatDateTime(incident.start_time)}</td>
                <td style={tdStyle}>{incident.end_time ? formatDateTime(incident.end_time) : '-'}</td>
                <td style={tdStyle} style={{ ...tdStyle, fontWeight: '500' }}>
                  {formatDuration(incident.duration_seconds)}
                </td>
                <td style={tdStyle}>
                  <Badge variant={incident.qualifies_as_downtime ? 'danger' : 'warning'}>
                    {incident.qualifies_as_downtime ? 'Downtime Valid (>5m)' : 'Transient / Ignored'}
                  </Badge>
                </td>
                <td style={tdStyle}>
                  <Badge variant={incident.qualifies_as_downtime ? 'danger' : 'warning'}>
                    {incident.root_error_category || 'Koneksi Gagal'}
                  </Badge>
                </td>
                <td style={tdStyle} style={{ ...tdStyle, fontSize: '0.825rem', color: '#9ca3af', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={incident.root_error_message}>
                  {incident.root_error_message || '-'}
                </td>
                <td style={tdStyle}>
                  {incident.incident_status === 'ACTIVE' ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#ef4444', fontWeight: '600', fontSize: '0.85rem' }}>
                      <AlertCircle size={14} /> AKTIF
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#10b981', fontWeight: '600', fontSize: '0.85rem' }}>
                      <CheckCircle2 size={14} /> SELESAI
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default IncidentTable;
