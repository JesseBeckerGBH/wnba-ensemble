import { useState, useEffect } from 'react';

/**
 * A hook designed to seamlessly transition to a real WebSocket stream.
 * For now, it pulses mock data according to the "aggression" profile of the selected model.
 */
export const useTelemetryStream = (modelType) => {
  const [data, setData] = useState({ edge: 0, status: 'IDLE' });

  useEffect(() => {
    let interval;
    if (modelType === 'laferrari') {
      // High volatility, Relativistic shifts (Darts)
      interval = setInterval(() => {
        const spike = Math.random() > 0.85 ? Math.random() * 30 : Math.random() * 5;
        const status = spike > 20 ? '>>> MOMENTUM SHIFT <<<' : 'OCR: TRACKING';
        
        setData({ edge: spike, status });

        // Trigger Rumble physically on the device if high severity
        if (spike > 20 && navigator.vibrate) {
            navigator.vibrate([200, 100, 200, 100, 300]);
        }
      }, 500);
    } else if (modelType === 'berlinetta') {
      // Lower volatility, slow calculated Statistical edge (WNBA/Golf)
      setData({ edge: 5.5, status: 'MODELS ALIGNED' }); // starting state
      interval = setInterval(() => {
        setData(prev => {
          const shift = (Math.random() - 0.5) * 1.5;
          const newEdge = Math.max(0, Math.min(15, prev.edge + shift));
          const status = newEdge > 8 ? 'FAVORABLE ALIGNMENT' : 'AWAITING VALUE';
          return { edge: newEdge, status };
        });
      }, 3000);
    }

    return () => clearInterval(interval);
  }, [modelType]);

  return data;
};
