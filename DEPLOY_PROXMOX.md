# TT v2 — Proxmox Deployment Guide

## Prerequisites on the Proxmox VM
- Debian/Ubuntu LXC or VM
- Docker + Docker Compose installed
- At least 4 GB RAM, 20 GB disk recommended

---

## Step 1 — Install Docker on the VM (if not already done)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in, then verify:
docker run hello-world
```

---

## Step 2 — Copy the project to the VM

From your **Windows machine**, open a terminal in the `scratch/` folder and run:

```powershell
# Replace 192.168.1.X with your Proxmox VM's IP
scp -r . user@192.168.1.X:/opt/syndicate
```

Or use the Proxmox web UI to upload, or `git clone` if you've pushed it.

---

## Step 3 — Configure secrets

```bash
cd /opt/syndicate/node_tt_v2_engine

cp .env.template .env
nano .env   # Fill in BETSAPI_TOKEN
```

---

## Step 4 — Copy the pre-trained model & database

The model artifact and DuckDB are already in the repo.  
On the first `docker compose up`, Docker will copy them into the named volumes.  
If you ever retrain locally and want to push a new model:

```bash
# On VM — copy updated artifacts from host into the mounted path
cp /opt/syndicate/node_tt_v2_engine/artifacts/models/stack_*.pkl \
   /var/lib/docker/volumes/syndicate_tt_db/_data/   # adjust path as needed
```

---

## Step 5 — Build and run (just the TT node for now)

```bash
cd /opt/syndicate

# Build only the tt_v2 service (skip kafka/timescale for now)
docker compose build node_tt_v2

# Run it
docker compose up -d node_tt_v2

# Watch the logs
docker compose logs -f node_tt_v2
```

Expected output on first boot:
```
INFO | Starting TT_V2 Polyglot Inference Node [24/7 PROXMOX LOOP]
INFO | Polling TT Odds via Go Ingestion Binary...
INFO | Evaluating N active TT lines via Council of Prophets.
INFO | Loop completed. Sleeping for 1800 seconds.
```

---

## Step 6 — ONNX export (optional, for Rust-native inference)

On the VM (after the container is running):

```bash
# Install ONNX tools in the container
docker exec tt_node pip install skl2onnx onnx onnxruntime

# Export
docker exec tt_node python model/export_onnx.py

# The .onnx file will be at:
# /app/node_tt_v2_engine/artifacts/models/tt_stack.onnx
# which maps to the host path:
# /opt/syndicate/node_tt_v2_engine/artifacts/models/tt_stack.onnx
```

---

## Step 7 — Test a prediction manually

```bash
docker exec -it tt_node python model/predict.py \
  --player-a "Ma Long" --player-b "Fan Zhendong" \
  --sets-to-win 2 --odds-a 1.90
```

Expected output:
```
========================================================
  TT v2 — COUNCIL OF PROPHETS
========================================================
  Ma Long                       62.3%
  Fan Zhendong                  37.7%
  Score: 0-0

  Prophet breakdown:
    markov  0.623
    stack   0.618
    elo     0.641
  Agreement: 0.814  [Strong]
  Kelly mult: 1.00x
  Edge:  +8.37%  Kelly: 2.09%  Stake: $20.90
========================================================
```

---

## Step 8 — Run the full SYNDICATE stack (when ready)

```bash
cd /opt/syndicate
docker compose up -d
```

This starts: Zookeeper, Kafka, TimescaleDB, node_tt_v2, node_wnba, node_darts_cv, node_consensus.

---

## Useful commands

```bash
# Stop
docker compose stop node_tt_v2

# Restart
docker compose restart node_tt_v2

# Rebuild after code changes
docker compose up -d --build node_tt_v2

# Shell into the container
docker exec -it tt_node bash

# Re-run backtest (Julia required on VM or inside a Julia container)
julia node_tt_v2_engine/backtest/walkforward.jl \
  --data node_tt_v2_engine/data/match_features_v1.csv

# View health check status
docker inspect --format='{{json .State.Health}}' tt_node | python -m json.tool
```
