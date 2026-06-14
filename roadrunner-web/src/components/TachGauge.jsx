import React, { useState, useEffect, useRef } from 'react';

/**
 * TachGauge — SVG tachometer inspired by 1971 Plymouth RoadRunner gauge cluster.
 * Circular gauge with chrome bezel, numbered markings, redline zone, and animated needle.
 *
 * Props:
 *   value (0-100) - gauge reading percentage
 *   label - text below gauge (e.g. "WIN PROB", "EDGE", "AUC")
 *   displayValue - string to show in center (e.g. "67.4%")
 *   size (px) - gauge diameter
 *   redlineStart (0-100) - where the red zone begins
 *   revving - boolean to trigger rev animation
 */
export default function TachGauge({
  value = 0,
  label = '',
  displayValue = '',
  size = 180,
  redlineStart = 80,
  revving = false,
}) {
  const [currentValue, setCurrentValue] = useState(0);
  const animRef = useRef(null);

  useEffect(() => {
    // Animate needle on value change
    const start = currentValue;
    const end = Math.min(Math.max(value, 0), 100);
    const duration = 800;
    const startTime = performance.now();

    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrentValue(start + (end - start) * eased);
      if (progress < 1) {
        animRef.current = requestAnimationFrame(animate);
      }
    };

    animRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animRef.current);
  }, [value]);

  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 12;
  const innerRadius = radius - 18;

  // Gauge arc: 240 degrees (from -210° to 30°)
  const startAngle = -210;
  const endAngle = 30;
  const totalArc = endAngle - startAngle; // 240°
  const needleAngle = startAngle + (currentValue / 100) * totalArc;
  const redlineAngleStart = startAngle + (redlineStart / 100) * totalArc;

  const toRad = (deg) => (deg * Math.PI) / 180;

  // Tick marks
  const majorTicks = 9; // 0-8 (like RPM x1000)
  const ticks = [];
  for (let i = 0; i <= majorTicks; i++) {
    const pct = i / majorTicks;
    const angle = startAngle + pct * totalArc;
    const rad = toRad(angle);
    const isRedline = pct >= redlineStart / 100;

    // Outer tick point
    const x1 = cx + Math.cos(rad) * (innerRadius + 8);
    const y1 = cy + Math.sin(rad) * (innerRadius + 8);
    // Inner tick point
    const x2 = cx + Math.cos(rad) * (innerRadius - (i % 2 === 0 ? 8 : 3));
    const y2 = cy + Math.sin(rad) * (innerRadius - (i % 2 === 0 ? 8 : 3));
    // Number position
    const nx = cx + Math.cos(rad) * (innerRadius - 20);
    const ny = cy + Math.sin(rad) * (innerRadius - 20);

    ticks.push(
      <g key={`tick-${i}`}>
        <line
          x1={x1} y1={y1} x2={x2} y2={y2}
          stroke={isRedline ? '#FF1A1A' : '#F0F0E8'}
          strokeWidth={i % 2 === 0 ? 2.5 : 1.2}
          strokeLinecap="round"
        />
        {i % 2 === 0 && (
          <text
            x={nx} y={ny}
            fill={isRedline ? '#FF1A1A' : '#A8A8A8'}
            fontSize={size / 16}
            fontFamily="'Oswald', sans-serif"
            fontWeight="600"
            textAnchor="middle"
            dominantBaseline="central"
          >
            {i}
          </text>
        )}
      </g>
    );
  }

  // Redline arc
  const redStart = toRad(redlineAngleStart);
  const redEnd = toRad(endAngle);
  const redX1 = cx + Math.cos(redStart) * (innerRadius + 4);
  const redY1 = cy + Math.sin(redStart) * (innerRadius + 4);
  const redX2 = cx + Math.cos(redEnd) * (innerRadius + 4);
  const redY2 = cy + Math.sin(redEnd) * (innerRadius + 4);

  // Needle
  const needleRad = toRad(needleAngle);
  const needleLen = innerRadius - 6;
  const nx = cx + Math.cos(needleRad) * needleLen;
  const ny = cy + Math.sin(needleRad) * needleLen;
  // Counterweight
  const cwLen = 12;
  const cwx = cx - Math.cos(needleRad) * cwLen;
  const cwy = cy - Math.sin(needleRad) * cwLen;

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ filter: 'drop-shadow(0 0 8px rgba(0,0,0,0.6))' }}
      >
        {/* Chrome bezel outer ring */}
        <circle cx={cx} cy={cy} r={radius + 6} fill="none" stroke="#555" strokeWidth="3" />
        <circle cx={cx} cy={cy} r={radius + 3} fill="none" stroke="#A8A8A8" strokeWidth="1.5" />

        {/* Gauge face */}
        <circle cx={cx} cy={cy} r={radius} fill="#0A0A0A" />
        <circle cx={cx} cy={cy} r={radius - 1} fill="none" stroke="#222" strokeWidth="1" />

        {/* Redline arc */}
        <path
          d={`M ${redX1} ${redY1} A ${innerRadius + 4} ${innerRadius + 4} 0 0 1 ${redX2} ${redY2}`}
          fill="none"
          stroke="#FF1A1A"
          strokeWidth="4"
          opacity={currentValue >= redlineStart ? 1 : 0.6}
          className={currentValue >= redlineStart ? 'redline-zone' : ''}
        />

        {/* Tick marks + numbers */}
        {ticks}

        {/* Needle */}
        <line
          x1={cwx} y1={cwy} x2={nx} y2={ny}
          stroke="#FF6B00"
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{
            filter: currentValue >= redlineStart
              ? 'drop-shadow(0 0 4px #FF1A1A)'
              : 'drop-shadow(0 0 3px rgba(255,107,0,0.5))',
          }}
        />

        {/* Center cap (chrome hub) */}
        <circle cx={cx} cy={cy} r="8" fill="#333" stroke="#888" strokeWidth="1.5" />
        <circle cx={cx} cy={cy} r="4" fill="#555" />

        {/* Digital readout in center-bottom */}
        {displayValue && (
          <text
            x={cx}
            y={cy + radius * 0.35}
            fill="#39FF14"
            fontSize={size / 10}
            fontFamily="'Share Tech Mono', monospace"
            textAnchor="middle"
            dominantBaseline="central"
            style={{ filter: 'drop-shadow(0 0 4px rgba(57,255,20,0.5))' }}
          >
            {displayValue}
          </text>
        )}
      </svg>

      {label && (
        <span
          style={{
            marginTop: '0.3rem',
            fontSize: size / 14,
            color: '#FF6B00',
            fontFamily: "'Oswald', sans-serif",
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </span>
      )}
    </div>
  );
}
