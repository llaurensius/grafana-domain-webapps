import React from 'react';

const StatCard = ({ title, value, icon: Icon, color = '#6366f1', subtitle, statusIndicator }) => {
  const cardStyle = {
    backgroundColor: '#131520',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderLeft: `4px solid ${color}`,
    borderRadius: '12px',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    transition: 'all 0.2s',
    position: 'relative',
    overflow: 'hidden'
  };

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    color: '#9ca3af',
    fontSize: '0.875rem',
    fontWeight: '500'
  };

  const valueStyle = {
    fontSize: '2rem',
    fontWeight: '800',
    color: '#ffffff',
    fontFamily: 'Outfit, sans-serif',
    lineHeight: 1.2
  };

  const subtitleStyle = {
    fontSize: '0.75rem',
    color: '#9ca3af',
    marginTop: '0.25rem'
  };

  const glowStyle = {
    position: 'absolute',
    top: '-20px',
    right: '-20px',
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    backgroundColor: color,
    opacity: 0.05,
    filter: 'blur(20px)',
    pointerEvents: 'none'
  };

  return (
    <div 
      style={cardStyle}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = `0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 0 15px ${color}1a`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
      }}
    >
      <div style={glowStyle} />
      <div style={headerStyle}>
        <span>{title}</span>
        {Icon && <Icon size={20} style={{ color }} />}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
        <span style={valueStyle}>{value}</span>
        {statusIndicator}
      </div>
      {subtitle && <span style={subtitleStyle}>{subtitle}</span>}
    </div>
  );
};

export default StatCard;
