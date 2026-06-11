import React from 'react';

/**
 * CockpitDial - An analog gauge styled after a sports car RPM dial, 
 * showing the mathematical Edge percentage.
 */
const CockpitDial = ({ value, label = "EDGE %", maxValue = 100 }) => {
  // Calculate rotation (from -135deg to +135deg for a 270deg sweep)
  const clampedValue = Math.min(Math.max(value, 0), maxValue);
  const percentage = clampedValue / maxValue;
  const rotation = -135 + (percentage * 270);

  return (
    <div className="analog-dial-container">
      <div className="speedometer-bg"></div>
      
      {/* Dial Ticks (Simplified for React without SVGs) */}
      <svg width="100%" height="100%" viewBox="0 0 200 200" style={{ position: 'absolute', top: 0, left: 0 }}>
        {/* Arc indicating danger/high-edge zone */}
        <path d="M 30,170 A 100,100 0 0,1 170,170" fill="transparent" stroke="var(--rosso-corsa)" strokeWidth="6" strokeDasharray="10 5" opacity="0.4" />
      </svg>

      {/* The Needle */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: '4px',
        height: '80px',
        backgroundColor: 'var(--rosso-corsa)',
        transformOrigin: 'bottom center',
        transform: `translate(-50%, -100%) rotate(${rotation}deg)`,
        transition: 'transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)', // Springy physics
        boxShadow: '0 0 10px var(--rosso-corsa)',
        borderRadius: '2px'
      }}>
        {/* Needle center cap */}
        <div style={{
          position: 'absolute',
          bottom: '-6px',
          left: '-4px',
          width: '12px',
          height: '12px',
          backgroundColor: '#ccc',
          borderRadius: '50%',
          border: '2px solid #222'
        }}></div>
      </div>

      <div className="digital-readout dial-value" style={{ fontSize: '1.5rem', top: '55%' }}>
        {value.toFixed(1)}
      </div>
      <div className="dial-label">{label}</div>
    </div>
  );
};

export default CockpitDial;
