# Planner tools

Run these commands from the repository root. The tools are development helpers;
the app does not load them.

## Compare road paths

`compare_walks.py` uses only Python's standard library. Pass coordinates as
**latitude, longitude**, matching Find Route. It converts them to OSRM's
longitude/latitude order internally. No coordinates are hardcoded.

```bash
python3 tools/planner/compare_walks.py \
  --origin '7.0919,125.6105' \
  --destination '7.0994,125.6309'
```

Add the boarding and alighting points to compare the direct path with the two
walking parts of a possible jeep trip:

```bash
python3 tools/planner/compare_walks.py \
  --origin '7.0919,125.6105' \
  --destination '7.0994,125.6309' \
  --board '7.09145,125.61033' \
  --alight '7.09897,125.63077'
```

Both extra points are optional. Output is one JSON object per path, containing
`case` (`direct`, `access`, or `egress`), `distance_m`, `router_duration_s`, and
the distinct road names returned by the router. Requests run sequentially;
`--timeout 12` sets the per-request timeout. Any failed path produces an error
object and a nonzero exit status. Invalid coordinates are rejected before any
request. For negative coordinates, use `--origin=-7.25,125.50` if argument
parsing treats the leading minus as an option.

### Parameters

| Option | Default | Purpose |
| --- | --- | --- |
| `--origin LAT,LNG` | Required | Starting coordinate. |
| `--destination LAT,LNG` | Required | Target coordinate. |
| `--board LAT,LNG` | Omitted | Add the origin-to-boarding comparison. |
| `--alight LAT,LNG` | Omitted | Add the alighting-to-destination comparison. |
| `--router-url URL` | `https://router.project-osrm.org` | OSRM server base URL, including an optional path prefix. |
| `--profile NAME` | `foot` | Profile name in the request URL; the server determines the actual transport mode. |
| `--timeout SECONDS` | `12` | Timeout for each request. |
| `--interval SECONDS` | `1` | Minimum time between request starts; follow the chosen provider's usage policy. |
| `--user-agent TEXT` | `DavaoRoutes-spike/1.0` | Identify the caller to the provider. |
| `--steps` / `--no-steps` | Enabled | Include turn steps and road names; disabled returns an empty roads list. |
| `--format jsonl` / `--format json` | `jsonl` | Stream individual JSON records, or print one JSON array. |

For example, another agent can use a locally hosted OSRM server and capture a
single JSON array:

```bash
python3 tools/planner/compare_walks.py \
  --origin '7.0919,125.6105' \
  --destination '7.0994,125.6309' \
  --router-url http://127.0.0.1:5000 \
  --profile driving --timeout 8 --interval 1 \
  --user-agent 'Route-investigation/1.0' \
  --no-steps --format json > /tmp/route-comparison.json
```

The command sends supplied coordinates to the configured router
(**router.project-osrm.org** by default); choose
points you intend to share with that service. It does not request device
location, save responses, identify jeep services, or calculate jeep fares.

The existing app endpoint uses `/route/v1/foot`, but OSRM's transport mode is
[fixed by the server's prepared routing profile](https://project-osrm.org/docs/v5.24.0/api/#general-options).
The path name alone does not verify pedestrian routing. Treat returned paths
as road-routing estimates and **do not interpret `router_duration_s` as walking
time**. Confirm foot access, crossings, gates, and actual jeep stops separately.

## Browser regression checks

Serve the app with `./run.sh`, then run:

```bash
uv run --with playwright python tools/planner/regression_checks.py
```

This runs Playwright Firefox and installed Google Chrome. Both need Leaflet's
CDN; map tiles and routing responses are mocked. It covers direct walks,
estimated access along jeep route lines, coordinate input, road-detour ranking,
the ordered journey result and its markers, and whole-journey playback (leg
order, marker switching, scrubbing, and the advancing animation). Use
`--browsers firefox` or `--browsers chromium` to select one browser, or
`--url http://127.0.0.1:8123/` for another app server. See
[`../geolocation/README.md`](../geolocation/README.md) for browser setup.
