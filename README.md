# Davao Jeep Routes

An interactive, single-file web app for exploring Davao City PUJ (jeepney) routes,
planning a commute, and animating a jeepney along the chosen road path.

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
  extra boardings, and allows limited walking between nearby stops.
- **Route animation** — play/pause, scrub, speed control (1x/2x/5x), and a
  follow-camera option that animates a jeepney marker along the route.
- **Geolocation** — "My Location" uses the browser Geolocation API, with a
  timeout guard so a stalled location service does not lock the UI.
- **Responsive layout** — sidebar panel + map, usable on desktop and mobile.

## Tech stack

| Layer | Choice |
| --- | --- |
| Markup/styling | HTML + [Tailwind CSS](https://tailwindcss.com/) via CDN |
| Mapping | [Leaflet](https://leafletjs.com/) 1.9.4 (unpkg CDN) |
| Tile layer | OpenStreetMap standard tiles |
| App logic | Vanilla JavaScript (no framework, no bundler) |
| Data storage | Route/landmark data inlined in `index.html` |
| Place lookup | Google Places API (New), optional key; OpenStreetMap Nominatim fallback |
| Local dev server | `run.sh` (Python `http.server` via `uv`) |
| Browser APIs | Geolocation, `requestAnimationFrame`, DOM, `fetch`, `localStorage` |

There is **no build step and no package manifest**. The app is one HTML file plus
a small server helper. Internet access is required for the Tailwind CDN, Leaflet
CDN, and OSM map tiles.

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

- **Playwright + headless Chromium/Chrome** — page-load, route-render, route
  selection, animation, and trip-planning checks. CLI helper `playwright-cli` is
  also available for interactive snapshots.
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
is optional and is stored only in the browser. All build scripts were temporary
and removed after the route data was written into `index.html`.

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

Last verified: **October 23, 2026**.

## Known limitations

- Coordinates are approximate boarding points; the planner snaps each landmark to
  the nearest point on a route.
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
- Browser geolocation on Linux Firefox can freeze the whole browser when the OS
  GeoClue service is missing. To avoid this, "My Location" on Linux Firefox asks
  you to tap your spot on the map (accurate, no native call) or type a starting
  point, instead of using the Geolocation API.

## Attribution

Map data © OpenStreetMap contributors. Leaflet is distributed under the BSD-2-Clause
license. Tailwind CSS is delivered via its CDN. No license file is included for
this project; add one if you plan to redistribute.
