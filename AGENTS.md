# AGENTS.md — Davao Jeep Routes

## Project
Single-file static web app (`index.html`) for exploring Davao City PUJ (jeepney)
routes, planning commutes, and animating a jeepney. No build step, no package
manifest. Serve with `./run.sh [port]` (default 8000). Full documentation:
`README.md`.

## Start here

- Read `README.md` for the current app behavior and development stack, and
  `ROADMAP.md` for product direction, open investigations, and deferred work.
- Read `HANDOVER.md` when present for the latest checkpoint and unfinished work;
  verify its snapshot against the current working tree before continuing.
- Familiarize yourself with the saved tools before creating new diagnostics:
  run `rg --files tools`, read `tools/geolocation/README.md` and
  `tools/planner/README.md`, and inspect the relevant script or its `--help` output.
- Discover the browser tools exposed in the current agent session. Editor MCP
  configuration does not guarantee that the same MCP is available to the agent.
- Check `git status --short` and preserve existing uncommitted work.

## Key facts
- All app logic, data, planner, map, and animation live in `index.html`, in
  banner-labelled layers: backend (`DATA`, `GEOMETRY & TEXT`, `PLACES`,
  `SERVICES`, `PLANNER`, `JOURNEY`) then frontend (`PANEL VIEW`, `MAP VIEW`,
  `ANIMATION`, `CONTROLLER`). Put new domain code in the backend layers and new
  rendering in the frontend layers; read the static tables through `StaticData`
  and build journeys through `JourneyBuilder`/`buildJourney`.
- Route/landmark data and planner tuning constants are inlined near the landmarks
  block (`MAX_ACCESS_WALK`, `MAX_TRANSFER_WALK`, `BOARDING_PENALTY`,
  `WALK_COST_MULTIPLIER`, `PREFER_DIRECT_WALK`, `MAX_RIDE_CANDIDATES`,
  `WALK_ROUTING_TIMEOUT`).
- Routes are stored as `[lat, lng]` pairs; planner treats each route as
  bidirectional between consecutive stops.
- Walk display uses OSRM road geometry when `walkMode === 'roads'`, with
  straight-line connectors as fallback. The `foot` URL alone does not verify
  the server's pedestrian profile; see `tools/planner/README.md`.
  Google Maps walking link is always shown.
- Place lookup order: local landmarks → Google Places (New, optional key) →
  OSM Nominatim fallback. Decimal `latitude, longitude` input is parsed locally;
  a bare pair is a destination, while `from <pair> to <place>` sets the origin.
- Nearby boarding/alighting points are inferred from route geometry as well as
  named landmarks. Access points are estimates. Shortlist up to three jeep
  itineraries using straight-line costs, then compare routed road distances
  before choosing. Prefer direct walks of 500 m or less; unavailable routing
  falls back to labeled estimates. Boarding penalties apply to transfers.
- The destination uses a separate Leaflet marker with an inline SVG flag and
  permanent label. Keep it visible while locating or reporting an unsupported
  trip, and clear it when returning to route exploration or an origin-only state.
- The intended playback covers the full walking/jeep journey. Currently a trip
  animates only its first ride through `activeRoute` and `animationRange`.
  Path-intersection matching and static markers are steps toward complete
  multi-leg animation, which remains pending; see `HANDOVER.md` and `ROADMAP.md`.
- The intended planner output is one organized journey with origin, destination,
  ordered tagged waypoints, and connected walk/ride paths. Map rendering and
  playback should consume that result; the full contract is in `HANDOVER.md`
  and remains to be implemented.

## Dev / verification

Start the app with `./run.sh 8000` (uv + Python's threaded `http.server`). Use an
existing server when it already serves this checkout. Serve over localhost for
browser checks and geolocation.

| Tool | Use it for |
| --- | --- |
| `tools/planner/regression_checks.py` | Direct walks, nearby route access, coordinate input, road-detour ranking, transfer costs, deduplication, routing fallback, and stale-plan cancellation. |
| `tools/planner/compare_walks.py` | Reusable OSRM comparison of direct, boarding-access, and alighting-egress paths; configure coordinates, router, profile, timeout, interval, user agent, steps, and JSON output through CLI parameters. See `tools/planner/README.md`. |
| `tools/geolocation/regression_checks.py` | Mocked location ordering, cleanup, cancellation, denial, timeout, and destination preservation. |
| `tools/geolocation/native_probe.py` | Installed Firefox's native `getCurrentPosition` provider path. |
| `tools/geolocation/watch_probe.py` | Native location updates and coarse/precise estimate ordering. |
| `tools/geolocation/app_probe.py` | Repeated native location requests through the actual app. |
| `playwright-cli` | Interactive page snapshots, input, browser inspection, and screenshots; consult the available skill before using it. |
| Node.js | Syntax verification of the app's inline JavaScript. |

Run the saved browser regressions from the repository root with the server running:

```bash
uv run --with playwright python tools/planner/regression_checks.py
uv run --with playwright python tools/geolocation/regression_checks.py
```

Both default to Playwright Firefox and installed Google Chrome (`chromium` with
`channel=chrome`). They launch their own isolated browsers; CDP is not required.
Both accept `--browsers firefox`, `--browsers chromium`, and
`--url http://127.0.0.1:8123/`. Playwright Firefox must be installed; setup is
documented in `tools/geolocation/README.md`. Add `--offline` to `uv run` when
the required dependencies are already cached and network resolution is unwanted.
The checks still load Leaflet from its CDN; tiles are blocked and OSRM is mocked.

Syntax-check the inline app script without adding generated files:

```bash
python3 - <<'PY' | node --check
from pathlib import Path
import re
scripts = re.findall(r'<script>(.*?)</script>', Path('index.html').read_text(), re.S)
assert scripts, 'No inline app script found'
print('\n'.join(scripts))
PY
```

Run checks relevant to the change. For documentation-only edits, verify paths
and commands plus `git diff --check`; browser regressions need not be repeated.

### Native geolocation diagnostics

Use `network-local` for routine provider checks:

```bash
python3 tools/geolocation/native_probe.py network-local
python3 tools/geolocation/watch_probe.py network-local --headful
python3 tools/geolocation/app_probe.py network-local --headful
```

Run native probes sequentially: they share ports **8001** and **2833**. The app
probe expects the app on **8000**. They use temporary profiles and the installed
Firefox; `FIREFOX_BINARY` overrides the executable path.

Read the diagnostic README before using real-provider modes (`network`,
`default`, or `geoclue`). Real modes may send public-IP and nearby Wi-Fi details
to a provider. Keep raw profiles and logs under `/tmp`, outside the repository;
they may contain coordinates, network details, and provider keys.

Mocked checks and local-provider success establish code behavior, not reliable
real location. Firefox real-location reliability remains open. GeoClue was
removed from this development system at the user's request; it is not an app
dependency. Consult the investigation in `ROADMAP.md` before changing providers.

## Interactive debugging

Use Firefox for user-visible inspection unless the user requests another browser.
Zed has Firefox DevTools MCP (`@mozilla/firefox-devtools-mcp-moz`) configured.
When Firefox MCP is exposed in the agent session, inspect its available tools
and pages before opening a new window. Use it for page snapshots, interactions,
JavaScript evaluation, and inspection. If it cannot start or attach, report the
failure and use the saved Playwright checks or native probes as appropriate.

Chrome DevTools MCP is an optional alternative when available. For CDP inspection:

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
- Update relevant documentation before preparing a commit diff or draft: keep
  `README.md` behavior and verification notes current, record roadmap progress
  and remaining limits in `ROADMAP.md`, and update this guide when tools or
  workflows change. Only record checks that were actually run.
