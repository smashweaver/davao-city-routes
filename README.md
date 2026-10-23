# Davao Jeep Routes

An interactive, single-file web app for exploring Davao City PUJ (jeepney) routes,
planning a commute, and animating a jeepney along the chosen road path.

This repository is an exploratory spike for a planned public app, with
advertising as the intended monetization model. The product inspiration is a
Singapore transit app that brings bus and train routes together in one place;
the Davao spike begins with local jeepney routes. Product direction and
milestones are recorded in [`ROADMAP.md`](ROADMAP.md#product-direction).

The app ships five verified routes, a simple trip planner, and a map with an
animated jeepney marker.

**Live demo:** <https://smashweaver.github.io/davao-city-routes/>

## Features

- **Route map** — all routes drawn as colored polylines on an OpenStreetMap base map.
- **Natural-language trip search** — e.g. `Abreeza`, `from Matina to Abreeza`,
  `Bankerohan to Calinan`, `Uyanguren to SPMC`.
- **Place lookup for unknown names** — known landmarks resolve locally; other
  places are looked up with Google Places (when a key is saved) or OpenStreetMap
  Nominatim, then shown as pickable candidates with route-coverage hints.
- **Trip planner** — Dijkstra over a stop graph. It supports transfers, penalizes
  extra boardings, and allows limited walking between nearby stops. It also
  considers nearby access points along mapped jeep route lines, so a boarding
  walk need not end at a named landmark. Short direct walks compete with rides.
- **Route animation** — play/pause, scrub, speed control (1x/2x/5x), and a
  follow-camera option that animates a jeepney marker along the route.
- **Geolocation** — "My Location" watches for a fix with reported accuracy of
  500 m or better, stops after accepting it, and offers a manual fallback if
  location is unavailable or remains too broad for 12 seconds.
- **Responsive layout** — a paper-and-green route guide beside the map on desktop;
  a map above the planner on mobile. Styling lives in the HTML, with no CSS framework.

## Tech stack

| Layer | Choice |
| --- | --- |
| Markup/styling | Semantic HTML + self-contained native CSS in `index.html` |
| Mapping | [Leaflet](https://leafletjs.com/) 1.9.4 (unpkg CDN) |
| Tile layer | OpenStreetMap standard tiles |
| App logic | Vanilla JavaScript (no framework, no bundler) |
| Data storage | Route/landmark data inlined in `index.html` |
| Place lookup | Google Places API (New), optional key; OpenStreetMap Nominatim fallback |
| Walking paths | OSRM HTTP API, with straight-line connectors when unavailable |
| Local dev server | `run.sh` (Python `http.server` via `uv`) |
| Browser APIs | Geolocation, `requestAnimationFrame`, DOM, `fetch`, `localStorage` |

There is **no build step and no package manifest**. The app is one HTML file plus
a small server helper. Internet access is required for the Leaflet CDN and OSM
map tiles; application styling does not require a network request.

Development and verification tooling:

| Purpose | Tool |
| --- | --- |
| Editor | Zed |
| Firefox browser MCP | Firefox DevTools MCP (`@mozilla/firefox-devtools-mcp-moz`), configured in Zed |
| Chrome browser MCP | Chrome DevTools MCP, optional through the CDP setup in `AGENTS.md` |
| Browser regression checks | Playwright with Firefox and installed Google Chrome; `playwright-cli` for interactive checks |
| Real Firefox location diagnostics | Python standard library + Marionette, using isolated browser profiles |
| JavaScript syntax verification | Node.js `node --check` |

Browser MCP servers and diagnostic tools are used during development; visitors
only run the web app. GeoClue was investigated and then removed from the local
development system. The app requests location through the browser Geolocation API.
The planned public release and ad-supported revenue model are recorded in
[`ROADMAP.md`](ROADMAP.md#product-direction).

## Getting started

```bash
# from the repository root
./run.sh          # serves on http://localhost:8000
./run.sh 8123     # or choose a port
```

Then open <http://localhost:8000/>.

You can also open `index.html` directly, but a local HTTP server is recommended:
browsers often block or degrade geolocation on `file://`.

## Place lookup

Typed places are resolved in this order:

1. **Local landmarks** — the aliases in `index.html` (fast, no network).
2. **Google Places API (New)** — used when a key is saved in **Search settings**.
   The key stays in this browser's `localStorage`; it is never written to the
   repository. Enable *Places API (New)* in Google Cloud, enable billing, and
   restrict the key by HTTP referrer.
3. **OpenStreetMap Nominatim** — no-key fallback, bounded to the Davao City area
   and limited to one request per second. Results are cached for 7 days.

Candidates show their address, source, and nearest mapped stop. Selecting one
plans the trip; if it is outside the supported route network, the app says so.
A direct **Google Maps** search link is shown when no candidate is found.

Google Places API usage is billed by Google. Nominatim is free but subject to its
[usage policy](https://operations.osmfoundation.org/policies/nominatim/).

## Project structure

```
DavaoRoutes/
├── index.html   # entire application (UI, data, planner, map, animation)
├── run.sh       # threaded local static server (default port 8000)
├── README.md
├── ROADMAP.md   # product direction, milestones, and investigation findings
├── tools/
│   ├── geolocation/ # native Firefox probes and mocked browser regression checks
│   └── planner/     # direct-walk and nearby route-access regression checks
└── AGENTS.md    # notes for coding agents
```

## Routes in the dataset

All lengths are the road-path lengths computed by the app from the stored
coordinates. Fares are indicative renditions of posted/commonly charged ranges.

| id | Name | Length | Fare | Stops (in order) |
| --- | --- | --- | --- | --- |
| `sasa` | Sasa via J.P. Laurel | ~10.9 km | ₱15–₱25 | C.M. Recto → Victoria Plaza → Abreeza → SPMC → SM Lanang → Sasa Wharf |
| `toril` | Toril via McArthur Highway | ~18.6 km | ₱15–₱35 | Bankerohan → C.M. Recto → Ateneo de Davao → Roxas Night Market → Quezon Blvd → SM City → Matina Crossing → Ulas → Puan → Toril |
| `buhangin` | Buhangin / Indangan | ~15.0 km | ₱15–₱25 | Roxas Night Market → Gaisano Mall Bajada → Buhangin Flyover → Indangan |
| `mintal` | Mintal / Calinan | ~31.6 km | ₱20–₱45 | Bankerohan → Bangkal → Ulas → Mintal → Calinan |
| `route10` | Route 10 (Claveria – SPMC) | ~20.4 km | ₱15 flat | Claveria → Magallanes → Uyanguren → Quezon Blvd → Leon Garcia → Cabaguio → SPMC → J.P. Laurel → Ponciano → San Pedro → Bankerohan → C.M. Recto |

Routes are stored as `[lat, lng]` coordinate pairs and rendered as polylines.
The planner treats each route as bidirectional between consecutive stops.
For each trip, it projects the origin and destination onto each nearby route
line and splits the graph's ride edges at those points. These temporary access
points do not change the landmark dataset. Instructions label them as estimated
road access, since route geometry alone does not confirm a designated stop.
Trip costs include riding distance, walking distance, and boarding penalties;
a direct walk of up to `MAX_ACCESS_WALK` is also considered.

### Planner tuning

Defined near the landmarks block in `index.html`:

| Constant | Value | Purpose |
| --- | --- | --- |
| `MAX_ACCESS_WALK` | 1600 m | Max walk from a typed/current location to a boarding stop |
| `MAX_TRANSFER_WALK` | 1400 m | Max walk when transferring between stops |
| `BOARDING_PENALTY` | 4200 | Cost added for each new boarding, discouraging unnecessary transfers |
| `WALK_COST_MULTIPLIER` | 3 | Makes walking "costlier" than the same distance ridden |

## Data sources and provenance

Route geometry was built with the public **OSRM** driving profile and then
cross-checked against official/community descriptions:

- **Toril** — LTFRB Memorandum Circular 2020-024, Annex C (interim bus loop),
  adjusted to the jeepney variant via Quirino / Gen. Luna / Bonifacio; segment
  names and lengths verified against OSRM steps.
- **Sasa** — CommuteTour "Sasa via J.P. Laurel" description plus place
  coordinates from Google Maps.
- **Buhangin / Indangan** — OSM Wiki Davao public transport route notes; runs via
  J.P. Laurel, Buhangin Flyover, and Cabantian–Bunawan Road.
- **Mintal / Calinan** — Davao City government PHABS/Mintal route article; uses
  the older Mintal–Bago Gallera road rather than the newer Talomo–Puan bypass.
- **Route 10** — Metro Davao commute guide and OSM Wiki: *Claveria – SPMC
  Southbound Loop* (Magallanes, Uyanguren, Quezon Blvd, Leon Garcia, Cabaguio,
  SPMC, J.P. Laurel, Ponciano, San Pedro, Bankerohan).

Reference links:

- LTFRB MC 2020-024 (Annex C) — `davaocity.gov.ph`
- Davao City PHABS / Mintal bus augmentation — `davaocity.gov.ph`
- OSM Wiki: Davao City public transportation
- CommuteTour: Sasa via J.P. Laurel
- Reddit r/davao: Metro Davao Commute Guide
- OSRM demo router (road geometry), Nominatim/Overpass (cross-checks)

### New bypass roads

The dataset intentionally keeps jeepneys on established PUJ corridors:

- **Davao City Bypass Construction Project** (Sirawan/Toril–J.P. Laurel, Panabo)
  is not open for general traffic; full operation is targeted for 2028.
- **Davao City Coastal Road** bars PUVs/jeepneys (public utility vehicles have
  been excluded since July 19, 2023).
- Newer private-car bypasses (e.g. Diversion Road–Buhangin–Tigatto, Mamay–La
  Verna) are not treated as jeepney routes.

## Tools used while building this solution

This app was produced and verified with the following tools:

Saved geolocation diagnostics and browser regression checks are in
[`tools/geolocation/`](tools/geolocation/README.md), with runnable commands and
the current investigation findings.

- **Playwright + Firefox and Chromium/Chrome** — page-load, route-render, route
  selection, animation, trip-planning, and mocked geolocation checks. CLI helper
  `playwright-cli` is also available for interactive snapshots.
- **Firefox DevTools MCP / Chrome DevTools MCP** — browser inspection tooling;
  Firefox MCP is configured in Zed, and the optional Chrome CDP workflow is
  documented in `AGENTS.md`.
- **Installed Firefox + Marionette** — real-provider and local-provider location
  probes that disable automation's usual geolocation overrides.
- **OSRM public router API** — generated road-following polylines
  (`overview=full&geometries=geojson`) and step-by-step street verification.
- **Google Maps** — preferred source for place coordinates (Sasa Wharf, Indangan,
  Calinan, etc.).
- **Nominatim / Overpass** — cross-checks for street and barangay geometry.
- **Python via `uv`** — coordinate fetching, projection math, monotonic
  stop-progress validation, and formatting the inlined route arrays.
- **Node.js** — `node --check` on the extracted `<script>` for syntax validation.
- **Web search** — official/community route descriptions and bypass-road status.

No API key is required for the default OpenStreetMap lookup. A Google Places key
is optional and is stored only in the browser. Route-data build scripts were
temporary and removed after the route data was written into `index.html`.

## Verification performed

- Every route object has finite cumulative distances and non-empty coordinates.
- Every landmark referenced by a route exists, and no route repeats a landmark.
- Each route's named stops project onto its polyline in increasing order, with
  small offsets (mostly < 120 m).
- In headless Chromium: the page loads with no console/page errors, all five
  routes select and animate, and representative trips resolve
  (e.g. `Bankerohan to Calinan`, `Uyanguren to SPMC`,
  `Roxas Night Market to Sasa Wharf`).
- Place lookup: `savemore` returns Bangkal/Bunawan candidates via Nominatim;
  selecting Bangkal plans `Abreeza → Savemore`; Google Places parsing was tested
  with a mocked response; unknown places show the Google Maps search fallback.
- In Firefox and installed Chrome: mocked location-flow checks cover precise
  versus coarse updates, watch cleanup, repeated requests, denial, timeout,
  cancellation, destination preservation, and route-line map selection. Real
  Firefox diagnostics have returned a precise Wi-Fi estimate, but repeated real
  location reliability is still unresolved; see `tools/geolocation/README.md`.
- Planner checks reproduce a shared-stop detour, verify a single
  direct walking leg with recalculated distance and geometry endpoints, and
  ensure jeepney trips retain their rides and access/egress walking. They also
  cover an approximate Flores-area origin, route-edge splitting in both
  directions, estimated access labels, and query isolation.

Run the planner regression checks with the app served by `./run.sh`,
Playwright's Firefox installed, and installed Google Chrome (or use
`--browsers firefox` to check Firefox alone):

```bash
uv run --with playwright python tools/planner/regression_checks.py
```

Last verified: **October 24, 2026** (location, direct-walk, and route-access checks;
earlier route checks on October 23).

## Known limitations

- Coordinates are approximate boarding points; the planner snaps each landmark to
  the nearest point on a route.
- Nearby road access is inferred from route geometry. It does not verify legal
  stops, the correct side of the road, pedestrian entrances, or safe crossings.
  Selection uses straight-line walking estimates; OSRM geometry is requested
  after choosing the trip and does not yet affect candidate ranking.
- Routes are modeled as bidirectional lines even where the real service is a
  one-way loop (notably Route 10 southbound).
- Fares are indicative, not an LTFRB fare matrix.
- The cost model may prefer a short walk plus a shorter route over a very long
  direct loop (for example `Claveria → SPMC` via Route 10 vs walk + Buhangin).
- No live traffic, schedules, or real-time vehicle tracking.
- Geocoded places can be ambiguous (for example multiple Savemore branches);
  the app shows candidates instead of guessing.
- Google Places requires an API key, billing, and the *Places API (New)* service.
  Nominatim is rate-limited, so repeated new searches can take about a second.
- Typed place queries are sent to the selected geocoding provider.
- Place lookup may be blocked on `file://`; use `./run.sh` as recommended.
- Requires internet for the CDN assets, map tiles, and place lookup.
- Linux Firefox location reliability remains under investigation. A missing
  GeoClue session agent blocked client creation, and real network-provider tests
  have produced both precise Wi-Fi fixes and unusably broad IP estimates. The
  app waits for a usable automatic fix; typing an origin remains available.

## Attribution

Map data © OpenStreetMap contributors. Leaflet is distributed under the BSD-2-Clause
license. No license file is included for this project; add one if you plan to redistribute.
