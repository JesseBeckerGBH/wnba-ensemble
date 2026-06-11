import { WebSocketServer } from 'ws';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const API_KEY = process.env.ODDS_API_KEY;
const SPORT = 'mma_mixed_martial_arts'; // or basketball_wnba
const REGIONS = 'us';
const MARKETS = 'h2h';

const wss = new WebSocketServer({ port: 8080 });
console.log(`🚀 OCTAGON: Live Feed Adapter running on ws://localhost:8080`);
console.log(`📡 Polling The-Odds-API for ${SPORT}...`);

let latestOdds = null;

async function fetchOdds() {
    try {
        const response = await axios.get(`https://api.the-odds-api.com/v4/sports/${SPORT}/odds/`, {
            params: {
                apiKey: API_KEY,
                regions: REGIONS,
                markets: MARKETS,
                oddsFormat: 'decimal'
            }
        });

        const games = response.data;
        if (games && games.length > 0) {
            // Pick the first upcoming/live game
            const game = games[0];
            const bookmaker = game.bookmakers.find(b => b.key === 'pinnacle') || game.bookmakers[0];
            
            if (bookmaker && bookmaker.markets[0].outcomes.length >= 2) {
                const outcomes = bookmaker.markets[0].outcomes;
                const probA = 1 / outcomes[0].price;
                const probB = 1 / outcomes[1].price;
                
                // Normalize probabilities
                const totalProb = probA + probB;
                const normalizedProbA = probA / totalProb;
                const normalizedProbB = probB / totalProb;

                latestOdds = {
                    event: `${game.home_team} vs ${game.away_team}`,
                    combatants: { 
                        a: outcomes[0].name, 
                        b: outcomes[1].name 
                    },
                    win_prob_a: normalizedProbA,
                    win_prob_b: normalizedProbB,
                    market_edge: 0.04 // Placeholder for model edge vs market
                };
            }
        } else {
             // Fallback simulated odds if no active games are found from API
            latestOdds = {
                event: 'UFC Live (Simulated fallback)',
                combatants: { a: 'Fighter A', b: 'Fighter B' },
                win_prob_a: 0.55,
                win_prob_b: 0.45,
                market_edge: 0.05
            };
        }
    } catch (error) {
        console.error('Error fetching from The-Odds-API:', error.message);
    }
}

// Fetch immediately and then every 30 seconds to respect API rate limits
fetchOdds();
setInterval(fetchOdds, 30000);

wss.on('connection', function connection(ws) {
    console.log('Client connected to live stream.');

    if (latestOdds) {
        ws.send(JSON.stringify({
            type: 'INIT',
            timestamp: new Date().toISOString(),
            event: latestOdds.event,
            combatants: latestOdds.combatants,
            win_prob_a: latestOdds.win_prob_a,
            win_prob_b: latestOdds.win_prob_b,
            market_edge: latestOdds.market_edge
        }));
    }

    // Since real odds update slowly, we send simulated high-frequency ticks based on the real baseline 
    // to keep the frontend "live ticker" visually active for the customer demo.
    let currentProbA = latestOdds ? latestOdds.win_prob_a : 0.55;
    
    const interval = setInterval(() => {
        // Only drift slightly around the real market probability
        const anchorProb = latestOdds ? latestOdds.win_prob_a : 0.55;
        const drift = (Math.random() - 0.5) * 0.01; 
        currentProbA = Math.max(0.01, Math.min(0.99, currentProbA * 0.9 + anchorProb * 0.1 + drift));
        const currentProbB = 1 - currentProbA;

        let isMajorEvent = false;
        let majorEventMessage = "exchange";
        if (Math.random() > 0.98) {
            isMajorEvent = true;
            majorEventMessage = "ODDS SHIFT!";
        }

        ws.send(JSON.stringify({
            type: 'TICK',
            timestamp: new Date().toISOString(),
            live_event: majorEventMessage,
            is_major: isMajorEvent,
            win_prob_a: currentProbA.toFixed(3),
            win_prob_b: currentProbB.toFixed(3),
            edge: (currentProbA - (anchorProb - 0.02)).toFixed(3)
        }));
    }, 850);

    ws.on('close', () => {
        clearInterval(interval);
        console.log('Client disconnected.');
    });
});
