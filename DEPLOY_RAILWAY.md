# Deploying the WNBA Stack on Railway

This repo ships two deployable pieces. The cleanest Railway setup is **two
services in the same repo**, each with its own *Root Directory*:

| Service        | Root Directory      | Builder    | Serves                                |
|----------------|---------------------|------------|---------------------------------------|
| Frontend       | `killershades-web`  | nixpacks   | React/Vite dashboard (static)         |
| Inference API  | `node_wnba_engine`  | Dockerfile | FastAPI `/predict` over the model     |

Each service reads the `railway.toml` in its Root Directory
(`killershades-web/railway.toml` and `node_wnba_engine/railway.toml`).

---

## 1. Frontend dashboard service

1. New service → deploy from this repo.
2. **Settings → Root Directory** = `killershades-web`.
3. Railway picks up `killershades-web/railway.toml`:
   - nixpacks runs `npm install` + `npm run build`
   - start: `npm run preview -- --host 0.0.0.0 --port $PORT`
4. The dashboard currently fetches `/wnba_predictions.json` (a static file in
   `public/`). To point it at the live API instead, set the build-time var
   `VITE_WS_URL` (used by `LaFerrariCockpit.jsx`) or change the `fetch()` in
   `BerlinettaCockpit.jsx` to the inference API's public URL.

> The old config ran `npm run dev` (a dev server that ignores `$PORT`). The
> committed configs now do a production build + `vite preview`, and
> `vite.config.js` sets `preview.allowedHosts: true` so Railway's
> `*.up.railway.app` domain is accepted.

---

## 2. Inference API service

1. New service → deploy from this repo.
2. **Settings → Root Directory** = `node_wnba_engine`.
3. Railway picks up `node_wnba_engine/railway.toml` → builds `Dockerfile.api`:
   - installs `requirements-api.txt` (lean: no scrapers / Windows-only deps)
   - runs `uvicorn serve:app --host 0.0.0.0 --port $PORT`
   - health check: `GET /health`
4. Endpoints once live:
   - `GET  /`        → banner + loaded model versions
   - `GET  /health`  → readiness probe
   - `POST /predict` → JSON body, e.g.
     ```json
     { "home": "Las Vegas Aces", "away": "New York Liberty",
       "ml_home": 1.65, "ml_away": 2.30,
       "total_line": 162.5, "over_odds": 1.91, "under_odds": 1.91 }
     ```
   - `GET  /predict?home=Las%20Vegas%20Aces&away=New%20York%20Liberty`

### Data persistence (important)

`predict()` reads team features from a DuckDB file. The image bakes a snapshot
at `db/wnba.duckdb`, so the API works out of the box — but that snapshot is
**frozen**. For fresh predictions during the season you need one of:

- **Railway Volume** mounted at e.g. `/data`, then set `WNBA_DB_PATH=/data/wnba.duckdb`
  and run the ingest/feature/train pipeline (cron/worker) to refresh it; or
- **Railway Postgres** — port `ingest_wnba.py` / `build_features.py` /
  `predict.py` off DuckDB onto the managed Postgres add-on.

Without one of these, the API keeps returning predictions from the baked-in
data snapshot.

### Environment variables (set in the Railway dashboard, never commit)

Only needed if you also run ingestion / the odds loop / sentiment in this
service — the bare `/predict` API needs none of these:

| Var | Used by |
|-----|---------|
| `WNBA_DB_PATH` | DB location override (set to your volume path) |
| `ODDS_DATA_API_KEY` / `BETS_API_KEY` | `scripts/odds_client.py` |
| `GEMINI_API_KEY` | consensus engine |
| `REDDIT_CLIENT_ID` / `TWITTER_USERNAME` | `sentiment/*` |
| `PAPER_TRADING_MODE`, `PAPER_STARTING_BANKROLL` | execution layer |

---

## 3. Optional: the 24/7 inference loop

`scripts/wnba_inference_loop.py` is a long-running worker (no HTTP) that polls
odds, predicts, and shells out to the Rust/C++ binaries. It is **not** wired
into the Railway services above — it suits a Railway *worker* service (no
public port) or the existing Proxmox/Docker stack. The Rust + C++ binaries are
not built by `Dockerfile.api`; build them separately or move that math into the
service if you want it on Railway.

---

## 4. ONNX artifacts

`model/export_onnx.py` converts the trained `.pkl` models to `.onnx`
(`pip install -r requirements-onnx.txt` first). ONNX only covers the
feature-vector → probability step; the feature engineering in `predict.py`
(DuckDB lookups, differentials, median imputation from the JSON sidecar) must
be reproduced by whatever runtime loads the `.onnx`. This lets you serve with
`onnxruntime` alone (tiny image) or run inference inside the Rust engine via the
`ort` crate instead of the Python hop.
