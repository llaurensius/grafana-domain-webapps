import React from 'react';

const StatCard = ({ title, value, icon, type = 'primary' }) => {
  return (
    <div className="card stat-card">
      <div className={`stat-icon ${type}`}>
        {icon}
      </div>
      <div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 600 }}>{title}</p>
        <h3 style={{ fontSize: '1.75rem', marginTop: '0.25rem' }}>{value}</h3>
      </div>
    </div>
  );
};

export default StatCard;
