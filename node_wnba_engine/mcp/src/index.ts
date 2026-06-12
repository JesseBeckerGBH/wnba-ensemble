#!/usr/bin/env node
/**
 * D:/WNBA/mcp/src/index.ts
 *
 * MCP server for WNBA ensemble predictions.
 * Exposes two tools:
 *   - run_wnba_prediction: predict a single game (moneyline + totals)
 *   - run_wnba_bet_sheet:  today's full bet sheet with Kelly stakes
 *
 * Install: cd D:/WNBA/mcp && npm install && npm run build
 * Run:     node dist/index.js
 *
 * Add to Claude Code MCP settings:
 * {
 *   "mcpServers": {
 *     "wnba": {
 *       "command": "node",
 *       "args": ["D:/WNBA/mcp/dist/index.js"]
 *     }
 *   }
 * }
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { execFileSync } from "child_process";
import * as path from "path";

const WNBA_ROOT = path.resolve(__dirname, "..", "..");
const PYTHON    = "py";
const PY_ARGS   = ["-3.13"];

function runPython(script: string, args: string[]): string {
  try {
    return execFileSync(PYTHON, [...PY_ARGS, script, ...args], {
      cwd:      WNBA_ROOT,
      encoding: "utf8",
      timeout:  60_000,
    });
  } catch (err: any) {
    return err.stdout || err.message || String(err);
  }
}

// ── Tool definitions ──────────────────────────────────────────────────────────
const TOOLS: Tool[] = [
  {
    name: "run_wnba_prediction",
    description:
      "Predict a single WNBA game. Returns home win probability, " +
      "moneyline edge, predicted total direction, and Kelly stake recommendation.",
    inputSchema: {
      type: "object",
      properties: {
        home_team:   { type: "string", description: "Home team name (e.g. 'Las Vegas Aces')" },
        away_team:   { type: "string", description: "Away team name (e.g. 'New York Liberty')" },
        ml_home:     { type: "number", description: "Decimal odds for home win (e.g. 1.75)" },
        ml_away:     { type: "number", description: "Decimal odds for away win (e.g. 2.15)" },
        total_line:  { type: "number", description: "Total points line (e.g. 162.5)" },
        over_odds:   { type: "number", description: "Decimal odds for over (e.g. 1.91)" },
        under_odds:  { type: "number", description: "Decimal odds for under (e.g. 1.91)" },
      },
      required: ["home_team", "away_team"],
    },
  },
  {
    name: "run_wnba_bet_sheet",
    description:
      "Generate today's full WNBA bet sheet. Fetches live odds from The Odds API, " +
      "runs predictions on all upcoming games, and returns ranked bets with Kelly stakes.",
    inputSchema: {
      type: "object",
      properties: {
        bankroll: {
          type: "number",
          description: "Current bankroll in £/$ (default: 1000)",
          default: 1000,
        },
        min_edge: {
          type: "number",
          description: "Minimum edge to include a bet (default: 0.05)",
          default: 0.05,
        },
      },
    },
  },
  {
    name: "run_wnba_sentiment",
    description:
      "Fetch Reddit sentiment scores for two WNBA teams. " +
      "Useful for assessing player motivation, drama signals, injury concerns.",
    inputSchema: {
      type: "object",
      properties: {
        team_a: { type: "string", description: "First team name" },
        team_b: { type: "string", description: "Second team name (optional)" },
      },
      required: ["team_a"],
    },
  },
];

// ── Server ────────────────────────────────────────────────────────────────────
const server = new Server(
  { name: "wnba-ensemble", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  if (name === "run_wnba_prediction") {
    const a = args as any;
    const cliArgs = [
      "model/predict.py",
      "--home", a.home_team,
      "--away", a.away_team,
    ];
    if (a.ml_home)    cliArgs.push("--ml-home",    String(a.ml_home));
    if (a.ml_away)    cliArgs.push("--ml-away",    String(a.ml_away));
    if (a.total_line) cliArgs.push("--total-line", String(a.total_line));
    if (a.over_odds)  cliArgs.push("--over-odds",  String(a.over_odds));
    if (a.under_odds) cliArgs.push("--under-odds", String(a.under_odds));

    const output = runPython(cliArgs[0], cliArgs.slice(1));
    return { content: [{ type: "text", text: output }] };
  }

  if (name === "run_wnba_bet_sheet") {
    const a = args as any;
    const cliArgs = ["scripts/todays_bets.py",
      "--bankroll", String(a.bankroll ?? 1000),
    ];
    if (a.min_edge) cliArgs.push("--min-edge", String(a.min_edge));
    const output = runPython(cliArgs[0], cliArgs.slice(1));
    return { content: [{ type: "text", text: output }] };
  }

  if (name === "run_wnba_sentiment") {
    const a = args as any;
    const output = runPython("sentiment/reddit_monitor.py", [
      "--test", "--team", a.team_a,
    ]);
    return { content: [{ type: "text", text: output }] };
  }

  throw new Error(`Unknown tool: ${name}`);
});

// ── Start ─────────────────────────────────────────────────────────────────────
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("WNBA MCP server running on stdio");
}

main().catch(console.error);
