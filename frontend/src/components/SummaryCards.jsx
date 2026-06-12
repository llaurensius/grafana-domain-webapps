import React from 'react';
import { ShieldAlert, BarChart2, AlertOctagon } from 'lucide-react';
import Badge from './UI/Badge';

const SummaryCards = ({ summaryData }) => {
  const { top_affected_domains = [], error_distribution = {}, total_incidents, total_downtime_seconds } = summaryData;

  const containerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '1.5rem',
    marginTop: '1.5rem'
  };

  const cardStyle = {
    backgroundColor: '#131520',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '12px',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  };

  const titleStyle = {
    fontSize: '1.1rem',
    fontWeight: '600',
    marginBottom: '1.25rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#ffffff'
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0 detik';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} menit`;
    const hours = Math.floor(minutes / 60);
    const remMins = minutes % 60;
    return `${hours} jam ${remMins} m`;
  };

  // Hitung total error untuk menghitung persentase
  const totalErrors = Object.values(error_distribution).reduce((sum, val) => sum + val, 0);

  return (
    <div style={containerStyle}>
      {/* Card 1: Top Affected Domains */}
      <div style={cardStyle}>
        <h3 style={titleStyle}>
          <ShieldAlert size={18} color="#ef4444" />
          Top Affected Domains (Paling Berdampak)
        </h3>
        {top_affected_domains.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', minHeight: '200px' }}>
            Tidak ada domain yang terkena dampak gangguan pada periode ini.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', flex: 1 }}>
            {top_affected_domains.map((domain, index) => (
              <div 
                key={domain.domain_id} 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.04)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    backgroundColor: index === 0 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                    color: index === 0 ? '#ef4444' : '#9ca3af',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.8rem',
                    fontWeight: '700'
                  }}>
                    {index + 1}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                    <span style={{ fontWeight: '600', fontSize: '0.9rem' }}>{domain.domain_name}</span>
                    <span style={{ fontSize: '0.75rem', color: '#9ca3af', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {domain.target_url}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.15rem' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#ef4444' }}>
                    {formatDuration(domain.total_downtime_seconds)}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                    {domain.incident_count} insiden
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Card 2: Error Distribution */}
      <div style={cardStyle}>
        <h3 style={titleStyle}>
          <AlertOctagon size={18} color="#f59e0b" />
          Distribusi Kategori Error
        </h3>
        {totalErrors === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', minHeight: '200px' }}>
            Tidak ada data error untuk periode ini.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, justifyContent: 'center' }}>
            {Object.entries(error_distribution).map(([category, count]) => {
              const percentage = totalErrors > 0 ? (count / totalErrors) * 100 : 0;
              return (
                <div key={category} style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: '500' }}>
                    <span style={{ color: '#f3f4f6' }}>{category}</span>
                    <span style={{ color: '#9ca3af' }}>{count} kejadian ({percentage.toFixed(0)}%)</span>
                  </div>
                  {/* Progress Bar */}
                  <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${percentage}%`,
                      height: '100%',
                      backgroundColor: category.includes('HTTP 5xx') || category.includes('502') || category.includes('Error') || category.includes('0') ? '#ef4444' : '#f59e0b',
                      borderRadius: '4px',
                      transition: 'width 0.5s ease-out'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryCards;
