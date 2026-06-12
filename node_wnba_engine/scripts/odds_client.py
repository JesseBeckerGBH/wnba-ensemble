#!/usr/bin/env python3
"""
D:/WNBA/scripts/odds_client.py

Odds fetcher for WNBA — two sources:
  1. The Odds API  (sport key: basketball_wnba — COVERED by existing key)
  2. BetsAPI       (sport_id=18)

Usage:
    py -3.13 scripts/odds_client.py --upcoming          # list upcoming games + odds
    py -3.13 scripts/odds_client.py --upcoming --save   # save to DB
    py -3.13 scripts/odds_client.py --source betsapi    # use BetsAPI instead
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

import duckdb
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

DB_PATH          = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))
ODDS_API_KEY     = os.getenv("ODDS_API_KEY", "")
BETSAPI_TOKEN    = os.getenv("BETSAPI_TOKEN", "") or os.getenv("BetsAPI_Key", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; wnba-v1/1.0)",
    "Accept":     "application/json",
}


# ── The Odds API ──────────────────────────────────────────────────────────────
ODDS_API_BASE    = "https://api.the-odds-api.com/v4"
WNBA_SPORT_KEY   = "basketball_wnba"

def theodds_get_upcoming() -> list[dict]:
    """Fetch upcoming WNBA games with moneyline + totals odds."""
    if not ODDS_API_KEY:
        raise RuntimeError("ODDS_API_KEY not set in .env")

    params = {
        "apiKey":    ODDS_API_KEY,
        "regions":   "us,uk,eu",
        "markets":   "h2h,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }
    url = (f"{ODDS_API_BASE}/sports/{WNBA_SPORT_KEY}/odds/?"
           + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())

    events = []
    for ev in data:
        home  = ev.get("home_team", "?")
        away  = ev.get("away_team", "?")
        start = ev.get("commence_time", "")
        gid   = ev.get("id", "")

        best_home_ml  = None
        best_away_ml  = None
        total_line    = None
        best_over     = None
        best_under    = None

        for bm in ev.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market["key"] == "h2h":
                    for outcome in market.get("outcomes", []):
                        price = outcome.get("price")
                        if outcome["name"] == home:
                            if best_home_ml is None or price > best_home_ml:
                                best_home_ml = price
                        elif outcome["name"] == away:
                            if best_away_ml is None or price > best_away_ml:
                                best_away_ml = price

                elif market["key"] == "totals":
                    for outcome in market.get("outcomes", []):
                        total_line = outcome.get("point", total_line)
                        price = outcome.get("price")
                        if outcome["name"] == "Over":
                            if best_over is None or price > best_over:
                                best_over = price
                        elif outcome["name"] == "Under":
                            if best_under is None or price > best_under:
                                best_under = price

        events.append({
            "source":       "theodds",
            "game_id":      gid,
            "home":         home,
            "away":         away,
            "start":        start,
            "home_ml":      best_home_ml,
            "away_ml":      best_away_ml,
            "total_line":   total_line,
            "over_odds":    best_over,
            "under_odds":   best_under,
            "bookmakers":   len(ev.get("bookmakers", [])),
        })

    return events


# ── BetsAPI ───────────────────────────────────────────────────────────────────
BETSAPI_BASE  = "https://api.betsapi.com/v1"
WNBA_SPORT_ID = "18"

def _betsapi_get(path: str, params: dict = None) -> dict:
    if not BETSAPI_TOKEN:
        raise RuntimeError("BETSAPI_TOKEN not set in .env")
    p = {"token": BETSAPI_TOKEN, "sport_id": WNBA_SPORT_ID}
    if params:
        p.update(params)
    url = f"{BETSAPI_BASE}/{path}?{urllib.parse.urlencode(p)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    if data.get("success") != 1:
        raise RuntimeError(f"BetsAPI error: {data}")
    return data


def betsapi_get_upcoming(max_events: int = 50) -> list[dict]:
    events = []
    page   = 1
    while len(events) < max_events:
        raw = _betsapi_get("events/upcoming", {"page": page}).get("results", [])
        if not raw:
            break
        for ev in raw:
            if len(events) >= max_events:
                break
            home     = ev.get("home", {}).get("name", "?")
            away     = ev.get("away", {}).get("name", "?")
            event_id = str(ev.get("id", ""))
            start_ts = ev.get("time")
            start_dt = (datetime.utcfromtimestamp(int(start_ts)).strftime("%Y-%m-%d %H:%M UTC")
                        if start_ts else "?")

            home_ml = away_ml = total_line = over_odds = under_odds = None
            try:
                odds_raw = _betsapi_get("event/odds/summary", {"event_id": event_id})
                market   = (odds_raw.get("results", {}).get("end")
                            or odds_raw.get("results", {}).get("start")
                            or {}).get("1_1", {})
                home_ml = _best_price(market.get("1", []))
                away_ml = _best_price(market.get("2", []))
                time.sleep(0.5)
            except Exception:
                pass

            events.append({
                "source":      "betsapi",
                "game_id":     event_id,
                "home":        home,
                "away":        away,
                "start":       start_dt,
                "home_ml":     home_ml,
                "away_ml":     away_ml,
                "total_line":  total_line,
                "over_odds":   over_odds,
                "under_odds":  under_odds,
                "bookmakers":  0,
            })
        page += 1

    return events


def _best_price(odds_list: list):
    prices = []
    for entry in odds_list:
        try:
            v = float(entry.get("odds") or entry.get("o") or 0) if isinstance(entry, dict) else float(entry)
            if v > 1.0:
                prices.append(v)
        except (TypeError, ValueError):
            pass
    return max(prices) if prices else None


# ── Save to DB ─────────────────────────────────────────────────────────────────
def save_odds(conn: duckdb.DuckDBPyConnection, events: list[dict]):
    saved = 0
    for ev in events:
        if not ev.get("home_ml"):
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO odds
                (game_id, source, bookmaker, home_ml, away_ml,
                 total_line, over_odds, under_odds, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                ev["game_id"], ev["source"], ev["source"],
                ev["home_ml"], ev["away_ml"],
                ev.get("total_line"), ev.get("over_odds"), ev.get("under_odds"),
            ],
        )
        saved += 1
    return saved


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="WNBA odds client")
    p.add_argument("--upcoming", action="store_true", help="Fetch upcoming games + odds")
    p.add_argument("--source",   choices=["theodds", "betsapi"], default="theodds")
    p.add_argument("--save",     action="store_true", help="Save odds to DuckDB")
    args = p.parse_args()

    if args.upcoming:
        print(f"\n[odds] Fetching upcoming WNBA games from {args.source}...")
        if args.source == "betsapi":
            events = betsapi_get_upcoming()
        else:
            events = theodds_get_upcoming()

        print(f"\n  Found {len(events)} events\n")
        print(f"  {'Start':20s} {'Home':28s} {'HO':6s} {'Away':28s} {'AO':6s} {'Line':6s}")
        print("  " + "─" * 100)
        for ev in events:
            ho = f"{ev['home_ml']:.2f}" if ev["home_ml"] else "  -  "
            ao = f"{ev['away_ml']:.2f}" if ev["away_ml"] else "  -  "
            tl = f"{ev['total_line']:.1f}" if ev["total_line"] else "  -  "
            print(f"  {ev['start']:20s} {ev['home']:28s} {ho:6s} {ev['away']:28s} {ao:6s} {tl:6s}")

        if args.save:
            conn = duckdb.connect(DB_PATH)
            n = save_odds(conn, events)
            conn.commit()
            conn.close()
            print(f"\n  Saved {n} odds records to DB")


if __name__ == "__main__":
    main()
