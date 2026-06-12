import React from 'react';

const Badge = ({ children, type = 'success' }) => {
  return (
    <span className={`badge ${type}`}>
      {children}
    </span>
  );
};

export default Badge;
