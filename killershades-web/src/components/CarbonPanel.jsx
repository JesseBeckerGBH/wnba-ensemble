import React from 'react';

/**
 * CarbonPanel - Wraps children in the Scuderia Punk carbon fiber texture 
 * with stitched leather red accents. Aggressively premium.
 */
const CarbonPanel = ({ children, title = null, style = {} }) => {
  return (
    <div className="carbon-fiber" style={{ padding: '2px', ...style }}>
      <div className="stitched-leather" style={{ padding: '20px', height: '100%', boxSizing: 'border-box' }}>
        {title && (
          <h2 style={{ 
            color: 'var(--giallo-modena)', 
            marginTop: 0, 
            fontFamily: 'var(--font-dash)',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            borderBottom: '1px solid #333',
            paddingBottom: '10px'
          }}>
            {title}
          </h2>
        )}
        <div style={{ position: 'relative', zIndex: 1 }}>
          {children}
        </div>
      </div>
    </div>
  );
};

export default CarbonPanel;
