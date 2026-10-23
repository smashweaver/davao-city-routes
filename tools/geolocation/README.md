# Geolocation spike tools

These diagnostics were built while investigating native geolocation in Firefox
on Pop!_OS / COSMIC. They are development tools; the public web app does not load
them. No build step or package manifest is required.

## What is here

| File | Purpose |
| --- | --- |
| `native_probe.py` | Minimal page using the installed Firefox and native `getCurrentPosition`; prints provider preferences, heartbeat, result, accuracy, and latency. |
| `watch_probe.py` | Watches location updates for about 14 seconds to expose races between coarse IP and precise Wi-Fi estimates. |
| `app_probe.py` | Runs three location requests through the actual app and checks that useful fixes are accepted and watches stop. Exits unsuccessfully when real location is unavailable or too broad. |
| `regression_checks.py` | Mocked browser checks for precise/coarse result ordering, stale callbacks, cancellation, timeout, permission denial, destination preservation, and map fallback. |

The native probes use Python's standard library and Firefox's Marionette
interface. They create isolated profiles, disable automation's usual location
overrides, and leave your normal Firefox profile unchanged. They automatically
allow location access **only inside their temporary profile**.

## Local provider checks

Run the app in a separate terminal for app-level checks:

```bash
./run.sh 8000
```

From the repository root:

```bash
python3 tools/geolocation/native_probe.py network-local
python3 tools/geolocation/watch_probe.py network-local --headful
python3 tools/geolocation/app_probe.py network-local --headful
```

`network-local` is also the default when no mode is given. It points Firefox's
network location provider at a loopback mock server. The response uses a fixed
Davao coordinate; success proves the native code path works, not that the device
was located. The app probe's mock reports 14 m accuracy so it exercises the app's
500 m acceptance limit. The other probes report a deliberately distinct 1234 m.

Native probes default to headless. `--headful` opens a visible test window. Run
them sequentially: they use loopback ports **8001** and **2833**. The app probe
expects DavaoRoutes at `http://127.0.0.1:8000/`.

Firefox defaults to `/usr/lib/firefox/firefox`. Override it when necessary:

```bash
FIREFOX_BINARY=/path/to/firefox python3 tools/geolocation/native_probe.py network-local
```

## Real location checks

These modes send public-IP and potentially nearby Wi-Fi access-point information
to the configured location provider. `network` uses Firefox's built-in network
provider, which used Google in the tested installation. `default` keeps Firefox's
normal provider selection, including GeoClue when enabled; that service may have
its own external backend.

```bash
python3 tools/geolocation/native_probe.py network --headful
python3 tools/geolocation/watch_probe.py network --headful
python3 tools/geolocation/app_probe.py network --headful
python3 tools/geolocation/native_probe.py default --headful
```

The tools print accuracy and timing without printing exact device coordinates.
Raw Firefox logs and temporary profiles are saved under `/tmp/davao-native-geo-*`;
**raw logs may contain coordinates, network details, and provider API keys**.
New artifacts are created with private permissions. They are outside this repo;
do not commit them or publish them as test output. Native probe failures return
a nonzero exit status. A successful location response alone does not establish
adequate accuracy or freedom from intermittent failures.

## Mocked app regressions

These checks replace the page's Geolocation API; they do not request real device
location. They still need Leaflet from its CDN to load. Tile requests are
blocked, and OSRM requests use the app's offline walking fallback.

```bash
uv run --with playwright python -m playwright install firefox
uv run --with playwright python tools/geolocation/regression_checks.py
```

The default runs Firefox's Playwright build and the installed Google Chrome
(`chromium` with `channel=chrome`). Select one, or a different app server URL:

```bash
uv run --with playwright python tools/geolocation/regression_checks.py --browsers firefox
uv run --with playwright python tools/geolocation/regression_checks.py --browsers chromium --url http://127.0.0.1:8123/
```

## Findings so far

- GeoClue 2.7.0 could not finish `Manager.GetClient` without a desktop permission
  agent. Starting the installed demo agent reduced that request from a timeout
  to roughly 50 ms. This fixes client creation, not provider accuracy.
- Installed Firefox 158.0.1 successfully used a local provider in headless and
  visible windows, with automation's location overrides disabled.
- A real Google-provider watch produced both a roughly **14 m** Wi-Fi estimate
  and a roughly **99 km** IP estimate. Their arrival order varied.
- A later real app run received only broad estimates and failed its accuracy
  check. **Repeated real-location reliability is still unresolved.**
- Mocked location-flow checks passed in Firefox and installed Chrome. These are
  app logic regressions, not evidence of real location accuracy.

The earlier temporary tests for the removed Firefox map-only workaround, and the
duplicate Chrome-only regression launcher, are superseded by the tools above.
