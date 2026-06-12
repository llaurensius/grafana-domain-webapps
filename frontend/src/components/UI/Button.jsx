import React from 'react';

const Button = ({ variant = 'primary', children, loading, style = {}, ...props }) => {
  const getStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: '#6366f1',
          color: '#ffffff',
          border: '1px solid transparent',
          cursor: 'pointer'
        };
      case 'secondary':
        return {
          backgroundColor: '#1b1e30',
          color: '#f3f4f6',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          cursor: 'pointer'
        };
      case 'danger':
        return {
          backgroundColor: '#ef4444',
          color: '#ffffff',
          border: '1px solid transparent',
          cursor: 'pointer'
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: '#f3f4f6',
          border: '1px solid rgba(255, 255, 255, 0.15)',
          cursor: 'pointer'
        };
      default:
        return {
          backgroundColor: '#9ca3af',
          color: '#111827',
          border: '1px solid transparent',
          cursor: 'pointer'
        };
    }
  };

  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.625rem 1.25rem',
    fontSize: '0.95rem',
    fontWeight: '500',
    borderRadius: '8px',
    transition: 'all 0.2s',
    outline: 'none',
    opacity: props.disabled || loading ? 0.6 : 1,
    pointerEvents: props.disabled || loading ? 'none' : 'auto',
    ...getStyles(),
    ...style
  };

  return (
    <button
      style={baseStyle}
      onMouseEnter={(e) => {
        if (variant === 'primary') e.target.style.backgroundColor = '#4f46e5';
        else if (variant === 'danger') e.target.style.backgroundColor = '#dc2626';
        else if (variant === 'secondary' || variant === 'outline') e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
      }}
      onMouseLeave={(e) => {
        const resetStyles = getStyles();
        e.target.style.backgroundColor = resetStyles.backgroundColor;
      }}
      {...props}
    >
      {loading ? (
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <svg style={{ animate: 'spin 1s linear infinite', width: '16px', height: '16px' }} viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" strokeDasharray="31.415, 31.415" />
          </svg>
          Loading...
        </span>
      ) : children}
    </button>
  );
};

export default Button;
