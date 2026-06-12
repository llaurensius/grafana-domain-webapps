import React from 'react';
import { Edit2, Trash2, Power, PowerOff } from 'lucide-react';
import Badge from './UI/Badge';

const DomainTable = ({ domains, onEdit, onDelete, onToggleActive }) => {
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

  const actionButtonStyle = (variant) => ({
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '32px',
    height: '32px',
    borderRadius: '6px',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    color: variant === 'danger' ? '#ef4444' : variant === 'success' ? '#10b981' : '#9ca3af',
    cursor: 'pointer',
    marginRight: '0.5rem',
    transition: 'all 0.2s'
  });

  return (
    <div style={tableContainerStyle}>
      {domains.length === 0 ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#9ca3af' }}>
          Belum ada domain terdaftar. Tambahkan domain baru untuk memulai monitoring.
        </div>
      ) : (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Nama Domain</th>
              <th style={thStyle}>Target URL</th>
              <th style={thStyle}>Protokol</th>
              <th style={thStyle}>Interval Probe</th>
              <th style={thStyle}>Status Monitoring</th>
              <th style={thStyle} style={{ textAlign: 'right' }}>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {domains.map((domain) => (
              <tr 
                key={domain.id}
                style={{ transition: 'background-color 0.2s' }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.01)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <td style={tdStyle} style={{ ...tdStyle, fontWeight: '600' }}>{domain.name}</td>
                <td style={tdStyle}>
                  <a href={domain.target_url} target="_blank" rel="noopener noreferrer" style={{ color: '#3b82f6' }}>
                    {domain.target_url}
                  </a>
                </td>
                <td style={tdStyle}><Badge variant="info">{domain.protocol}</Badge></td>
                <td style={tdStyle}>{domain.probe_interval} detik</td>
                <td style={tdStyle}>
                  <Badge variant={domain.active ? 'success' : 'default'}>
                    {domain.active ? 'Aktif' : 'Nonaktif'}
                  </Badge>
                </td>
                <td style={tdStyle} style={{ ...tdStyle, textAlign: 'right' }}>
                  <button 
                    onClick={() => onToggleActive(domain)}
                    style={actionButtonStyle(domain.active ? 'default' : 'success')}
                    title={domain.active ? 'Matikan Monitor' : 'Aktifkan Monitor'}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.06)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)'}
                  >
                    {domain.active ? <PowerOff size={14} /> : <Power size={14} />}
                  </button>
                  <button 
                    onClick={() => onEdit(domain)}
                    style={actionButtonStyle('default')}
                    title="Ubah"
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.06)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)'}
                  >
                    <Edit2 size={14} />
                  </button>
                  <button 
                    onClick={() => onDelete(domain)}
                    style={actionButtonStyle('danger')}
                    title="Hapus"
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.15)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)'}
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DomainTable;
