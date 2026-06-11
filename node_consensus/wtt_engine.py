import os
import sys
import json
import logging
import asyncio
import google.generativeai as genai
import statistics

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("[!] CRITICAL ERROR: GEMINI_API_KEY missing from .env. Mocks disabled.")

genai.configure(api_key=API_KEY)

# 5 Custom Multimodal Personas mapped specifically for the Coton vs. Shinozuka WTT Match
WTT_PERSONAS = [
    {
        "name": "Tactical Fundamentals Specialist", 
        "instruction": "Evaluate the structural Table Tennis matchup. Focus intensely on Flavien Coton's high-fencing aggression vs. Hiroto Shinozuka's left-handed sharp angles. Ignore public sentiment."
    },
    {
        "name": "Market Sentiment Contrarian", 
        "instruction": "Identify if the European public is over-betting Coton exclusively based on regional hype. Outline the exact mathematically hidden value on Shinozuka's technical discipline."
    },
    {
        "name": "Situational Analyst", 
        "instruction": "Compute the probability impact of the tournament location (Tunis), rest disparity, final-round psychological fatigue, and historical match stress."
    },
    {
        "name": "Technical Momentum Agent", 
        "instruction": "Respect the velocity of live line movement. Assume massive sharp syndicate money has just shifted in favor of the flagged target player. Calculate the baseline shift."
    },
    {
        "name": "Bayesian Synthesizer", 
        "instruction": "Run a hypothetical Monte-Carlo interpolation. If Coton serves 10% faster on average, quantify how effectively Shinozuka's left-side defensive block neutralizes the advantage."
    }
]

async def call_wtt_agent(persona, contextual_intel):
    logger.info(f"[*] WTT Orchestrator Spawning Agent Node: {persona['name']}")
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        prompt = f"""
        {persona['instruction']}
        
        LIVE MATCH INTELLIGENCE / ANOMALY DATA:
        Target: {contextual_intel['target_team']}
        Market Delta Velocity: {contextual_intel['velocity']}% 
        
        Process this data. Output ONLY a raw float (e.g., 0.625) representing the meticulously calculated 'True Win Expected Probability'.
        """
        response = await model.generate_content_async(prompt)
        
        prob = float(response.text.replace('`', '').strip())
        logger.info(f"    -> [{persona['name']}] EV Output: {prob:.3f}")
        return prob
        
    except Exception as e:
        logger.error(f"[!] Target Agent [{persona['name']}] dropped offline: {e}")
        return None

async def orchestrate_wtt_consensus(contextual_intel):
    logger.warning(f"\n[>>>] WTT STOCHASTIC ENGINE ARMED -> Target: {contextual_intel['target_team']}")
    
    tasks = [call_wtt_agent(persona, contextual_intel) for persona in WTT_PERSONAS]
    results = await asyncio.gather(*tasks)
    
    valid_probs = [p for p in results if p is not None]
    
    if len(valid_probs) >= 3:
        median_prob = statistics.median(valid_probs)
        mean_prob = statistics.mean(valid_probs)
        
        logger.info(f"\n[=========================]\n[ MEDIAN EV: {median_prob:.3f} ]\n[=========================]")
        # Forward EV to C++ Execution Layer via RabbitMQ or Kafka Topic
    else:
        logger.error("[!] WTT Engine Abort: Insufficient LLM validation.")

def main():
    logger.info("[*] Polyglot Subsystem: WTT Orchestrator Booting...")
    
    if len(sys.argv) < 2:
        logger.error("[!] Error: You must pass a live JSON string payload to spin the engine. Exiting to enforce Security Protocols.")
        sys.exit(1)
        
    injected_payload = json.loads(sys.argv[1])
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(orchestrate_wtt_consensus(injected_payload))

if __name__ == "__main__":
    main()
