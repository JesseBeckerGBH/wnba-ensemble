import React from 'react';

/**
 * MuscleDash — Container panel that looks like a section of the RoadRunner's
 * vinyl dashboard. Chrome bezel border with vinyl interior texture.
 */
export default function MuscleDash({ title, icon, children, className = '' }) {
  return (
    <div
      className={`chrome-bezel ${className}`}
      style={{
        margin: '0.75rem',
        transition: 'box-shadow 0.3s ease',
      }}
    >
      {/* Title strip — chrome header bar */}
      {title && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1rem',
            background: 'linear-gradient(180deg, #2A2A2A 0%, #1A1A1A 100%)',
            borderBottom: '1px solid #333',
            borderTopLeftRadius: '10px',
            borderTopRightRadius: '10px',
          }}
        >
          {icon && <span style={{ color: '#FF6B00', fontSize: '1.1rem' }}>{icon}</span>}
          <span
            style={{
              fontFamily: "'Oswald', sans-serif",
              fontWeight: 600,
              fontSize: '0.8rem',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: '#FF6B00',
            }}
          >
            {title}
          </span>
        </div>
      )}

      {/* Inner gauge panel */}
      <div className="gauge-panel">{children}</div>
    </div>
  );
}
