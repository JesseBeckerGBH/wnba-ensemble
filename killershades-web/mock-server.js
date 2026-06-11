import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 8080 });
console.log('🚀 OCTAGON: Mock WebSocket Server running on ws://localhost:8080');

wss.on('connection', function connection(ws) {
  console.log('Client connected to mock stream.');
  
  let probA = 0.61; 
  let probB = 0.39; 

  ws.send(JSON.stringify({
    type: 'INIT',
    timestamp: new Date().toISOString(),
    event: 'UFC 314 Live',
    combatants: { a: 'Alexander Volkanovski', b: 'Diego Lopes' },
    win_prob_a: probA,
    win_prob_b: probB,
    market_edge: 0.06
  }));

  const interval = setInterval(() => {
    const shift = (Math.random() - 0.48) * 0.03; 
    probA = Math.max(0.1, Math.min(0.9, probA + shift));
    probB = 1 - probA;

    let isMajorEvent = false;
    let majorEventMessage = "";
    if (Math.random() > 0.95) {
        probA += 0.15;
        probB = 1 - probA;
        isMajorEvent = true;
        majorEventMessage = "KNOCKDOWN (Volkanovski)!";
    }

    ws.send(JSON.stringify({
      type: 'TICK',
      timestamp: new Date().toISOString(),
      live_event: isMajorEvent ? majorEventMessage : 'exchange',
      is_major: isMajorEvent,
      win_prob_a: probA.toFixed(3),
      win_prob_b: probB.toFixed(3),
      edge: (probA - 0.55).toFixed(3)
    }));
  }, 850);

  ws.on('close', () => {
    clearInterval(interval);
    console.log('Client disconnected.');
  });
});
