import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ReferenceLine,
} from 'recharts';

/**
 * PerfChart — Bankroll performance chart styled like a dyno graph.
 * Hemi orange area with phosphor green stroke.
 */
const MOCK_DATA = Array.from({ length: 30 }, (_, i) => {
  const base = 10000;
  const trend = i * 45;
  const noise = Math.sin(i * 0.8) * 300 + Math.cos(i * 1.4) * 150;
  return {
    day: `Day ${i + 1}`,
    bankroll: Math.round(base + trend + noise),
    bets: Math.floor(Math.random() * 8) + 2,
  };
});

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: '#1A1A1A',
        border: '1px solid #FF6B00',
        borderRadius: '6px',
        padding: '0.5rem 0.8rem',
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: '0.8rem',
      }}
    >
      <div style={{ color: '#A8A8A8', marginBottom: '0.25rem' }}>{label}</div>
      <div style={{ color: '#39FF14' }}>
        ${payload[0]?.value?.toLocaleString()}
      </div>
      {payload[0]?.payload?.bets && (
        <div style={{ color: '#FF6B00', fontSize: '0.7rem' }}>
          {payload[0].payload.bets} bets
        </div>
      )}
    </div>
  );
};

export default function PerfChart({ data = MOCK_DATA, height = 260 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="hemiGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FF6B00" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#FF6B00" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(255,255,255,0.05)"
          vertical={false}
        />
        <XAxis
          dataKey="day"
          tick={{ fill: '#666', fontSize: 10, fontFamily: "'Share Tech Mono', monospace" }}
          axisLine={{ stroke: '#333' }}
          tickLine={false}
          interval={4}
        />
        <YAxis
          tick={{ fill: '#666', fontSize: 10, fontFamily: "'Share Tech Mono', monospace" }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine
          y={10000}
          stroke="#FF6B00"
          strokeDasharray="6 4"
          strokeOpacity={0.3}
          label={{
            value: 'START',
            fill: '#FF6B00',
            fontSize: 10,
            fontFamily: "'Share Tech Mono', monospace",
          }}
        />
        <Area
          type="monotone"
          dataKey="bankroll"
          stroke="#39FF14"
          strokeWidth={2}
          fill="url(#hemiGrad)"
          dot={false}
          activeDot={{
            r: 4,
            fill: '#FF6B00',
            stroke: '#39FF14',
            strokeWidth: 2,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
