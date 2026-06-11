import os
import json
import time
import pandas as pd
import xgboost as xgb
from kafka import KafkaConsumer, KafkaProducer
import psycopg2
from cachetools import LRUCache
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# [AGENT REVIEW FIX]: Memory limit explicitly enforced to completely prevent OOM Docker crash
STATE_CACHE = LRUCache(maxsize=50000)
# Baseline threshold: e.g., line moves > 5% in 1 second (1000ms) indicates sharp action
SHARP_MONEY_THRESHOLD_PER_SEC = 0.05 

def connect_db():
    conn = None
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "syndicate_lake"),
                user=os.getenv("DB_USER", "syndicate_admin"),
                password=os.getenv("DB_PASS", "supersecretpassword"),
                host=os.getenv("DB_HOST", "timescaledb")
            )
            logger.info("[*] Successfully connected to TimescaleDB.")
            break
        except psycopg2.OperationalError as e:
            logger.warning(f"[*] Database not ready... retries left: {retries}")
            time.sleep(5)
            retries -= 1
    return conn

def init_xgboost_model():
    logger.info("[*] Initializing XGBoost Meta-Learner Layer...")
    model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05)
    return model

def check_line_manipulation(tick, producer):
    """
    Statefully tracks the derivative of odds velocity to flag sharp syndicate movement instantly.
    """
    try:
        # Defensive parsing to prevent KeyErrors
        bookmaker = tick.get("bookmaker_id")
        match_id = tick.get("match_id")
        team = tick.get("team")
        new_odds = float(tick.get("odds"))
        new_timestamp = int(tick.get("timestamp_ms"))

        if not all([bookmaker, match_id, team, new_odds, new_timestamp]):
            return 
            
        cache_key = f"{bookmaker}_{match_id}_{team}"
        
        if cache_key in STATE_CACHE:
            old_odds, old_timestamp = STATE_CACHE[cache_key]
            delta_t_ms = max(new_timestamp - old_timestamp, 1) # avoid division by zero
            delta_t_sec = delta_t_ms / 1000.0
            
            odds_velocity = abs(new_odds - old_odds) / delta_t_sec if delta_t_sec > 0 else 0
            
            if odds_velocity >= SHARP_MONEY_THRESHOLD_PER_SEC:
                logger.warning(f"[!] ANOMALY: Massive Line Acceleration Detected -> Velocity: {odds_velocity:.3f}/sec | Team: {team}")
                
                alert = {
                    "type": "sharp_money_alert",
                    "match_id": match_id,
                    "team": team,
                    "velocity": odds_velocity,
                    "timestamp_ms": new_timestamp,
                    "trigger_bookmaker": bookmaker
                }
                producer.send('anomalies_ticker', alert)
                producer.flush()

        # Update cache explicitly for next tick 
        STATE_CACHE[cache_key] = (new_odds, new_timestamp)
        
    except Exception as e:
        # [AGENT REVIEW FIX]: Drop bad ticks gracefully instead of terminating
        logger.error(f"[!] Ingestion Error - Malformed Tick Dropped: {e}")

def main():
    logger.info("[*] Starting Syndicate Node: XGBoost Tabular Processing Layer")
    db_conn = connect_db()
    kafka_servers = [os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")]
    
    consumer = KafkaConsumer(
        'odds_ticker',
        bootstrap_servers=kafka_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    producer = KafkaProducer(
        bootstrap_servers=kafka_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    model = init_xgboost_model()

    logger.info("[*] Node actively listening on Kafka topic 'odds_ticker' [...]")
    for message in consumer:
        tick = message.value
        check_line_manipulation(tick, producer)
        
if __name__ == "__main__":
    main()
