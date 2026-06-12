import React from 'react';
import { Shield, ShieldAlert, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import Badge from './UI/Badge';

const DomainStatusTable = ({ domains, latestMetrics, prometheusStatus, onRefresh }) => {
  const tableContainerStyle = {
    width: '100%',
    overflowX: 'auto',
    backgroundColor: '#131520',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    marginTop: '1.5rem'
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

  const formatLastCheck = (timestamp) => {
    if (!timestamp) return '-';
    // Format timestamp ke lokal time
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatLatency = (latency) => {
    if (latency === undefined || latency === null || latency === 0) return '-';
    return `${latency.toFixed(0)} ms`;
  };

  const getHttpStatusCodeBadge = (code) => {
    if (code === 0) return <Badge variant="danger">code 0 (failed)</Badge>;
    if (code >= 200 && code < 300) return <Badge variant="success">HTTP {code}</Badge>;
    if (code >= 300 && code < 400) return <Badge variant="info">HTTP {code}</Badge>;
    if (code >= 400 && code < 500) return <Badge variant="warning">HTTP {code}</Badge>;
    return <Badge variant="danger">HTTP {code}</Badge>;
  };

  // Tampilkan peringatan jika status integrasi terganggu
  if (prometheusStatus === 'offline') {
    return (
      <div style={{
        padding: '2.5rem',
        textAlign: 'center',
        backgroundColor: 'rgba(239, 68, 68, 0.05)',
        border: '1px solid rgba(239, 68, 68, 0.15)',
        borderRadius: '12px',
        color: '#ef4444',
        marginTop: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '0.75rem'
      }}>
        <ShieldAlert size={40} />
        <h3 style={{ color: '#ef4444', margin: 0 }}>Integrasi Prometheus Terganggu (Data Source Offline)</h3>
        <p style={{ color: '#9ca3af', fontSize: '0.9rem', maxWidth: '500px', margin: 0 }}>
          Sistem tidak dapat terhubung ke Prometheus API. Status domain yang ditampilkan di bawah mungkin tidak sinkron atau tidak valid. Silakan periksa container Prometheus Anda.
        </p>
        <button 
          onClick={onRefresh}
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#ef4444',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <RefreshCw size={14} /> Coba Hubungkan Kembali
        </button>
      </div>
    );
  }

  // Ambil hanya domain aktif untuk ditampilkan di status monitor
  const activeDomains = domains.filter(d => d.active);

  return (
    <div style={tableContainerStyle}>
      <div style={{ 
        padding: '1.25rem', 
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Status Domain Aktif Terkini</h3>
        <button 
          onClick={onRefresh}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            color: '#6366f1',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.85rem',
            fontWeight: '600'
          }}
        >
          <RefreshCw size={14} /> Refresh Manual
        </button>
      </div>
      {activeDomains.length === 0 ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#9ca3af' }}>
          Tidak ada domain aktif yang sedang dimonitor. Silakan aktifkan domain di menu Kelola Domain.
        </div>
      ) : (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Domain</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>HTTP Status</th>
              <th style={thStyle}>Latency (Rata-rata)</th>
              <th style={thStyle}>Pengecekan Terakhir (Lokal)</th>
              <th style={thStyle}>Kategori Gangguan</th>
            </tr>
          </thead>
          <tbody>
            {activeDomains.map((domain) => {
              const metric = latestMetrics[domain.id.toString()];
              const isUp = metric ? metric.probe_success : true; // default ke UP jika data belum meluncur
              const statusCode = metric ? metric.status_code : null;
              const latency = metric ? metric.response_time_ms : null;
              const lastCheck = metric ? metric.checked_at : null;
              
              // Klasifikasi error kustom frontend jika data down
              let errorCategory = '-';
              if (metric && !isUp) {
                // Sederhanakan klasifikasi error untuk tabel
                if (statusCode === 404) errorCategory = 'Not Found';
                else if (statusCode === 502) errorCategory = 'Bad Gateway';
                else if (statusCode >= 400 && statusCode < 500) errorCategory = `HTTP ${statusCode}`;
                else if (statusCode >= 500 && statusCode < 600) errorCategory = `HTTP ${statusCode}`;
                else if (!metric.dns_lookup_success) errorCategory = 'DNS Error';
                else if (!metric.connection_success) errorCategory = 'Connection Error';
                else if (latency >= 9500) errorCategory = 'Timeout';
                else errorCategory = 'Connection Reset / Failed';
              }

              return (
                <tr 
                  key={domain.id}
                  style={{ transition: 'background-color 0.2s' }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.01)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                      <span style={{ fontWeight: '600' }}>{domain.name}</span>
                      <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{domain.target_url}</span>
                    </div>
                  </td>
                  <td style={tdStyle}>
                    {metric ? (
                      isUp ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10b981', fontWeight: '600' }}>
                          <Wifi size={14} /> ONLINE
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#ef4444', fontWeight: '600' }}>
                          <WifiOff size={14} /> OFFLINE
                        </div>
                      )
                    ) : (
                      <div style={{ color: '#9ca3af', fontStyle: 'italic' }}>no data (pending)</div>
                    )}
                  </td>
                  <td style={tdStyle}>
                    {statusCode !== null && statusCode !== undefined ? getHttpStatusCodeBadge(statusCode) : '-'}
                  </td>
                  <td style={tdStyle}>
                    {formatLatency(latency)}
                  </td>
                  <td style={tdStyle}>
                    {formatLastCheck(lastCheck)}
                  </td>
                  <td style={tdStyle}>
                    {isUp ? '-' : <Badge variant="danger">{errorCategory}</Badge>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DomainStatusTable;
