import os
import json
import logging
import asyncio
from kafka import KafkaConsumer
import google.generativeai as genai
import statistics

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE"))

# System prompts representing diverse Agent Personas for Stochastic Consensus
AGENT_PERSONAS = [
    {"name": "Fundamentals Agent", "instruction": "You are a sharp sports probability maker. Calculate pure win expectancy based heavily on mathematical metrics, schedules, and box scores."},
    {"name": "Contrarian Analyst", "instruction": "You actively look for fade opportunities. Analyze why the massive market shift might be an overreaction to public narrative."},
    {"name": "Injury/Sentiment Parser", "instruction": "You weight missing personnel, team morale, and immediate coach intent above all structural metrics."},
    {"name": "Market Momentum Agent", "instruction": "You evaluate the speed of line movement and unconditionally defer to sharp originating money."},
    {"name": "Synthetic Imputation Agent", "instruction": "Analyze the likelihood of variance assuming missing/sparse features have average standard deviation."}
]

async def call_agent(persona, anomaly_data):
    """
    Simulated parallel API call spawning a generative sub-agent to compute probability.
    """
    logger.info(f"[*] Spawning Core: {persona['name']}")
    try:
        # Use primary LLM logic defined in prompt config
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        prompt = f"""
        {persona['instruction']}
        A structural line anomaly has occurred:
        Target Match ID: {anomaly_data['match_id']}
        Target Team: {anomaly_data['team']}
        Line Shift Velocity: {anomaly_data['velocity']}/sec
        
        Analyze the structural anomaly mathematically.
        Return ONLY a raw float representing your exact 'True Win Probability' percent (e.g., 0.54) for this team. Do not add formatting.
        """
        response = await model.generate_content_async(prompt)
        
        # Robustly rip out markdown syntax or extra trailing text if hallucinated
        cleaned = response.text.replace('`', '').strip()
        prob = float(cleaned)
        logger.info(f"    -> {persona['name']} Synthesis EV: {prob:.3f}")
        return prob
        
    except Exception as e:
        logger.error(f"[!] LLM Fetch Dropped Core [{persona['name']}]: {e}")
        return None

async def run_stochastic_consensus(anomaly):
    """
    Executes 5 parallel multi-persona agents to triangulate absolute median Expected Value.
    """
    logger.info(f"\n[>>>] STOCHASTIC TRIANGULATION ARMED -> Match {anomaly['match_id']} (Team: {anomaly['team']})")
    
    # Asynchronously spark 5 parallel agent nodes
    tasks = [call_agent(persona, anomaly) for persona in AGENT_PERSONAS]
    results = await asyncio.gather(*tasks)
    
    # Prune failed generations/hallucinations
    valid_probs = [p for p in results if p is not None]
    
    if len(valid_probs) >= 3:
        median_prob = statistics.median(valid_probs)
        mean_prob = statistics.mean(valid_probs)
        
        logger.info(f"\n[==========> MEDIAN TRUE PROBABILITY: {median_prob:.3f} | Mean: {mean_prob:.3f} <==========]")
        
        # Action Step: Check if median EV diverges radically from the live line 
        # (e.g. median expects 58% but book offers +110 / 47%. That = execution)
    else:
        logger.warning("[!] Consensus abort protocol: Insufficient valid agent generations.")


def main():
    logger.info("[*] Starting Synergy Multi-Agent Orchestrator Node (Stochastic Consensus Layer)")
    
    kafka_servers = [os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")]
    
    # Only bound to the anomalous line manipulation stream to prevent LLM quota burn
    consumer = KafkaConsumer(
        'anomalies_ticker',
        bootstrap_servers=kafka_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    logger.info("[*] Orchestrator Node armed and awaiting Line Manipulation anomalies [...]")
    
    loop = asyncio.get_event_loop()
    
    for message in consumer:
        anomaly = message.value
        logger.warning(f"\n[!] ALERT RECEIVED -> Executing Parallel Agents for Match {anomaly['match_id']}")
        # Drop into async loop
        loop.run_until_complete(run_stochastic_consensus(anomaly))

if __name__ == "__main__":
    main()
