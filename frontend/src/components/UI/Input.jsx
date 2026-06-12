import React from 'react';

const Input = ({ label, id, error, style = {}, ...props }) => {
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.35rem',
    marginBottom: '1rem',
    width: '100%'
  };

  const labelStyle = {
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#9ca3af',
  };

  const inputStyle = {
    padding: '0.625rem 0.875rem',
    backgroundColor: '#1b1e30',
    border: error ? '1px solid #ef4444' : '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '8px',
    color: '#f3f4f6',
    fontSize: '0.95rem',
    outline: 'none',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    ...style
  };

  const errorStyle = {
    fontSize: '0.75rem',
    color: '#ef4444',
    marginTop: '0.25rem'
  };

  return (
    <div style={containerStyle}>
      {label && <label htmlFor={id} style={labelStyle}>{label}</label>}
      <input
        id={id}
        style={inputStyle}
        onFocus={(e) => {
          if (!error) {
            e.target.style.borderColor = '#6366f1';
            e.target.style.boxShadow = '0 0 0 2px rgba(99, 102, 241, 0.2)';
          }
        }}
        onBlur={(e) => {
          if (!error) {
            e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)';
            e.target.style.boxShadow = 'none';
          }
        }}
        {...props}
      />
      {error && <span style={errorStyle}>{error}</span>}
    </div>
  );
};

export default Input;
