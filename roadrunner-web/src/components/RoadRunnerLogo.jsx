import React from 'react';

/**
 * RoadRunnerLogo — Stylized Road Runner bird with basketball.
 * SVG illustration combining the classic cartoon bird silhouette with NBA.
 */
export default function RoadRunnerLogo({ size = 120 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      style={{ filter: 'drop-shadow(0 0 12px rgba(255,107,0,0.4))' }}
    >
      {/* Speed lines */}
      <line x1="10" y1="50" x2="35" y2="50" stroke="#FF6B00" strokeWidth="2" opacity="0.4" />
      <line x1="5" y1="58" x2="30" y2="58" stroke="#FF6B00" strokeWidth="1.5" opacity="0.3" />
      <line x1="12" y1="66" x2="32" y2="66" stroke="#FF6B00" strokeWidth="1" opacity="0.2" />

      {/* Body — stylized bird running */}
      <path
        d="M45 75 Q50 45 70 38 Q85 33 90 40 L88 45 Q83 42 78 43 Q72 44 68 50
           L75 48 Q80 46 82 50 L78 52 Q74 50 70 53 L65 58
           Q60 65 55 70 Q50 75 45 78 Z"
        fill="#FF6B00"
      />

      {/* Crest / head tuft */}
      <path
        d="M88 40 L95 30 L92 38 L98 32 L93 42 L88 45 Z"
        fill="#FF6B00"
      />

      {/* Eye */}
      <circle cx="84" cy="43" r="3" fill="#0A0A0A" />
      <circle cx="85" cy="42" r="1" fill="#F0F0E8" />

      {/* Beak */}
      <path d="M90 44 L102 42 L90 47 Z" fill="#FFD700" />

      {/* Legs (running pose) */}
      <path
        d="M55 75 L48 90 L55 88 M60 73 L65 90 L72 88"
        stroke="#FF6B00"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* Basketball in talons */}
      <circle cx="70" cy="92" r="10" fill="#CC5500" stroke="#FF6B00" strokeWidth="1" />
      <path
        d="M60 92 Q70 85 80 92 M70 82 L70 102 M62 86 Q70 92 78 86"
        stroke="#1A1A1A"
        strokeWidth="0.8"
        fill="none"
      />

      {/* "BEEP BEEP" text */}
      <text
        x="96"
        y="56"
        fill="#39FF14"
        fontSize="7"
        fontFamily="'Russo One', sans-serif"
        transform="rotate(-15, 96, 56)"
        style={{ filter: 'drop-shadow(0 0 3px rgba(57,255,20,0.5))' }}
      >
        BEEP
      </text>
      <text
        x="98"
        y="64"
        fill="#39FF14"
        fontSize="6"
        fontFamily="'Russo One', sans-serif"
        transform="rotate(-10, 98, 64)"
        opacity="0.7"
      >
        BEEP!
      </text>
    </svg>
  );
}
