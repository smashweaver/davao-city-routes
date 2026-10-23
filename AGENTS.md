# AGENTS.md — Davao Jeep Routes

## Project
Single-file static web app (`index.html`) for exploring Davao City PUJ (jeepney)
routes, planning commutes, and animating a jeepney. No build step, no package
manifest. Serve with `./run.sh [port]` (default 8000). Full documentation:
`README.md`.

## Key facts
- All app logic, data, planner, map, and animation live in `index.html`.
- Route/landmark data and planner tuning constants are inlined near the landmarks
  block (`MAX_ACCESS_WALK`, `MAX_TRANSFER_WALK`, `BOARDING_PENALTY`,
  `WALK_COST_MULTIPLIER`).
- Routes are stored as `[lat, lng]` pairs; planner treats each route as
  bidirectional between consecutive stops.
- Walk segments: OSRM foot profile when `walkMode === 'roads'`, else
  straight-line connectors. Google Maps walking link always shown.
- Place lookup order: local landmarks → Google Places (New, optional key) →
  OSM Nominatim fallback.

## Dev / verification
- Syntax check extracted script: `node --check` on the `<script>` content.
- Headless checks: `playwright-cli` or `uv run --with playwright python ...`
  connecting over CDP to a Chrome launched with `--remote-debugging-port=9222`.
- Server: `./run.sh` (uv + Python `http.server`, threaded).

## Interactive debugging
For agent-assisted inspection, run the app under Chrome with remote debugging so a
Chrome DevTools MCP client (Zed, OpenCode, etc.) can attach while you code:

1. Start the app: `./run.sh 8000`
2. Launch Chrome with a debugging port (separate profile recommended):
   `google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/davao-chrome http://localhost:8000/`

Then point the MCP client at `http://127.0.0.1:9222` (e.g. pass
`--browserUrl http://127.0.0.1:9222` to `chrome-devtools-mcp`). Put the Chrome
window and editor side by side in a Pop!_OS workspace for live inspection while
the agent drives the page via the MCP. For quick headless checks without an MCP
client, use `playwright-cli`.

## Conventions
- Vanilla JS, no framework, no bundler. Keep changes in `index.html`.
- Prefer editing existing code over new files. Do not add build tooling.
- Geolocation/`file://` caveats: recommend `./run.sh`.
