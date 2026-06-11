# Kafka & Database Ingestion Webhooks (Golang)

Written in Go to handle massive, concurrent webhooks streaming Live Odds.
Responsible for instantaneously writing to TimescaleDB and the Kafka pipeline without dropping frames during high-volume Saturday slates.
