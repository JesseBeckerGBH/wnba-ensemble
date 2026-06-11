@echo off
echo [*] Initiating deployment for the 2026 Syndicate Stack...
docker-compose up -d --build
echo [*] Deployment complete! 
echo [*] TimescaleDB and Kafka are currently active.
echo [*] Run 'docker-compose logs -f node_xgboost' to monitor the predictive engine logic logs.
