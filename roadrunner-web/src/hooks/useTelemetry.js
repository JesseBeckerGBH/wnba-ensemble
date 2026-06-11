import { useState, useEffect, useRef } from 'react';

/**
 * useTelemetry — Simulates real-time telemetry data for dashboard gauges.
 * In production, this would connect to a WebSocket from the inference loop.
 *
 * Returns:
 *   winProb - current model confidence (0-100)
 *   edge - model edge percentage
 *   auc - model AUC metric
 *   bankroll - current paper bankroll
 *   betsToday - number of bets placed today
 *   winRate - rolling win rate
 *   status - 'IDLE' | 'SCANNING' | 'EDGE_FOUND' | 'EXECUTING'
 */
export default function useTelemetry() {
  const [data, setData] = useState({
    winProb: 0,
    edge: 0,
    auc: 0.72,
    bankroll: 10000,
    betsToday: 0,
    winsToday: 0,
    winRate: 0,
    status: 'IDLE',
    lastScan: null,
    activePick: null,
  });

  const intervalRef = useRef(null);

  useEffect(() => {
    // Simulate periodic updates
    const states = ['IDLE', 'SCANNING', 'SCANNING', 'EDGE_FOUND', 'EXECUTING', 'IDLE'];
    let stateIdx = 0;

    intervalRef.current = setInterval(() => {
      stateIdx = (stateIdx + 1) % states.length;
      const status = states[stateIdx];

      setData((prev) => {
        const newBankroll = prev.bankroll + (Math.random() - 0.45) * 80;
        const newBets = status === 'EXECUTING' ? prev.betsToday + 1 : prev.betsToday;
        const newWins = status === 'EXECUTING' && Math.random() > 0.42
          ? prev.winsToday + 1
          : prev.winsToday;

        return {
          winProb: status === 'EDGE_FOUND' ? 55 + Math.random() * 20 : prev.winProb * 0.95,
          edge: status === 'EDGE_FOUND' ? (Math.random() * 8 + 1) : prev.edge * 0.8,
          auc: 0.68 + Math.random() * 0.1,
          bankroll: Math.round(newBankroll * 100) / 100,
          betsToday: newBets,
          winsToday: newWins,
          winRate: newBets > 0 ? (newWins / newBets) * 100 : 0,
          status,
          lastScan: status === 'SCANNING' ? new Date().toLocaleTimeString() : prev.lastScan,
          activePick: status === 'EDGE_FOUND'
            ? ['BOS ML', 'OVER 224.5', 'MIL ML', 'UNDER 219.0'][Math.floor(Math.random() * 4)]
            : (status === 'IDLE' ? null : prev.activePick),
        };
      });
    }, 3000);

    return () => clearInterval(intervalRef.current);
  }, []);

  return data;
}
