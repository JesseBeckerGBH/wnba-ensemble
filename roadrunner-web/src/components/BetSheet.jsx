import React, { useState } from 'react';

/**
 * BetSheet — Displays upcoming picks in a styled table.
 * When a bet row is clicked, triggers the engine rev animation.
 */
const MOCK_BETS = [
  {
    id: 1, time: '7:00 PM', matchup: 'BOS vs LAL',
    pick: 'BOS ML', prob: 0.674, odds: 1.52, edge: 0.015,
    kelly: 0.032, wager: 320, status: 'LIVE',
  },
  {
    id: 2, time: '7:30 PM', matchup: 'MIL vs PHX',
    pick: 'OVER 228.5', prob: 0.612, odds: 1.91, edge: 0.088,
    kelly: 0.046, wager: 460, status: 'PENDING',
  },
  {
    id: 3, time: '8:00 PM', matchup: 'DEN vs GSW',
    pick: 'DEN ML', prob: 0.581, odds: 1.72, edge: 0.001,
    kelly: 0.011, wager: 110, status: 'PENDING',
  },
  {
    id: 4, time: '9:00 PM', matchup: 'DAL vs LAC',
    pick: 'UNDER 219.5', prob: 0.557, odds: 1.95, edge: 0.044,
    kelly: 0.023, wager: 230, status: 'PENDING',
  },
  {
    id: 5, time: '10:00 PM', matchup: 'SAC vs POR',
    pick: 'SAC ML', prob: 0.705, odds: 1.43, edge: -0.006,
    kelly: 0.000, wager: 0, status: 'NO EDGE',
  },
];

export default function BetSheet({ onRevEngine }) {
  const [selectedId, setSelectedId] = useState(null);

  const handleRowClick = (bet) => {
    setSelectedId(bet.id);
    if (bet.wager > 0 && onRevEngine) {
      onRevEngine(bet);
    }
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="bet-sheet">
        <thead>
          <tr>
            <th>Time</th>
            <th>Matchup</th>
            <th>Pick</th>
            <th>Prob</th>
            <th>Odds</th>
            <th>Edge</th>
            <th>Kelly %</th>
            <th>Wager</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {MOCK_BETS.map((bet) => (
            <tr
              key={bet.id}
              onClick={() => handleRowClick(bet)}
              style={{
                cursor: 'pointer',
                background: selectedId === bet.id
                  ? 'rgba(255, 107, 0, 0.1)'
                  : 'transparent',
              }}
            >
              <td style={{ color: '#A8A8A8' }}>{bet.time}</td>
              <td style={{ fontWeight: 'bold' }}>{bet.matchup}</td>
              <td className="hemi-accent" style={{ fontWeight: 'bold' }}>{bet.pick}</td>
              <td className="digital-readout">{(bet.prob * 100).toFixed(1)}%</td>
              <td>{bet.odds.toFixed(2)}</td>
              <td className={bet.edge >= 0 ? 'edge-positive' : 'edge-negative'}>
                {bet.edge >= 0 ? '+' : ''}{(bet.edge * 100).toFixed(1)}%
              </td>
              <td className="digital-readout-dim">{(bet.kelly * 100).toFixed(1)}%</td>
              <td className="digital-readout">
                {bet.wager > 0 ? `$${bet.wager}` : '—'}
              </td>
              <td>
                <span
                  style={{
                    fontSize: '0.7rem',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                    fontWeight: 'bold',
                    letterSpacing: '0.06em',
                    background:
                      bet.status === 'LIVE' ? 'rgba(57,255,20,0.15)' :
                      bet.status === 'PENDING' ? 'rgba(255,107,0,0.15)' :
                      'rgba(255,255,255,0.05)',
                    color:
                      bet.status === 'LIVE' ? '#39FF14' :
                      bet.status === 'PENDING' ? '#FF6B00' :
                      '#666',
                  }}
                >
                  {bet.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
