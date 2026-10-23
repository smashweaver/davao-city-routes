# Roadmap — Davao Jeep Routes

## Product direction

This project is an exploratory spike for a Davao commute app. The intention is
to turn the findings into a maintained app for public use, with advertising as
the revenue model.

- **Current stage:** validate route exploration, commute planning, automatic
  location, and the experience on desktop and mobile.
- **Public app:** carry the proven behavior and investigation findings forward
  into the version people will use publicly.
- **Monetization:** support the public app through ads. The ad provider,
  placements, and integration are still to be decided; ads are not implemented.

### Product inspiration

The inspiration is a Singapore transit app that brings bus and train routes
around the city into one place. Its name has not yet been recorded.

Use that experience as a reference for making Davao's transport network easy to
explore and journeys easy to plan. The current spike starts with local jeepney
routes; use the Singapore reference to guide the route map, search, and journey
planning experience as the public app develops.

### Milestones toward the public app

- [ ] Establish reliable real-device location and decide which browsers to support.
- [ ] Validate route information and trip results with real commute examples.
- [ ] Validate the mobile experience for everyday use.
- [ ] Plan and implement the public release and advertising integration.

## Firefox freezing (priority)

Symptom: page can lock up in Firefox (Linux), especially around geolocation and
map rendering. Clicking "My Location" has triggered the freeze both before and
after installing GeoClue; the underlying browser/OS cause is still unconfirmed.

### Status
- [x] Trigger identified: requesting browser geolocation on Linux Firefox has
      reproduced the freeze. Installing GeoClue did not resolve the report.
- [x] Identified and fixed missing GeoClue permission agent in this session.
- [x] Replaced the temporary Firefox map-only workaround with an automatic
      location watch that accepts fixes reporting accuracy of 500 m or better,
      cancels after success, and falls back after 12 seconds.
- [ ] Establish repeated real-location reliability before closing the Firefox
      issue; a JavaScript timer cannot recover a hung browser process.

### Native geolocation investigation — October 24, 2026

- Installed browser: Firefox 158.0.1 on Pop!_OS 24.04 / COSMIC; GeoClue 2.7.0.
- Confirmed blocker: the GeoClue desktop permission agent was absent from the
  running session. A direct D-Bus `Manager.GetClient` call timed out independently
  of the app. GeoClue 2.7.0 queues client creation until an agent registers.
- Started `/usr/libexec/geoclue-2.0/demos/agent` under the transient user service
  `geoclue-demo-agent.service`. The same D-Bus call now succeeds in about 0.05s.
  `/etc/xdg/autostart/geoclue-demo-agent.desktop` already exists for future logins;
  no additional autostart file was needed.
- GeoClue was subsequently purged from the development system at the user's
  request, including its configuration and autostart entry. The session agent
  was stopped. The Firefox direct-network-provider preference remains in place.
- A minimal page in the installed Firefox stayed responsive but timed out with
  the original GeoClue setup. The reported full-browser freeze has not yet been
  reproduced in this isolated test.
- Firefox's native network provider scanned nearby Wi-Fi and accepted a response
  from a strictly local mock endpoint in both headless and visible windows. This
  verifies the provider code path, not real location accuracy or Google access.
- Automation normally changes geolocation preferences. Diagnostic tests disable
  those recommended overrides (`remote.prefs.recommended=false`) to exercise real
  providers; ordinary mocked browser checks cannot establish that GPS works.
- Real Google-provider testing was explicitly approved. A minimal native watch
  reported a roughly 14 m Wi-Fi estimate and a roughly 99 km IP estimate nearly
  simultaneously; their order varied. A later real app request received only
  broad estimates and failed the app's accuracy check. The issue remains open.
- Configured the installed Firefox profile with
  `user_pref("geo.provider.use_geoclue", false);` in its `user.js` to use the
  direct network provider. No custom Google API key or global permission grant
  was added to the normal profile.
- Saved runnable diagnostic tools, mocked browser regressions, and instructions
  in [`tools/geolocation/`](tools/geolocation/README.md). The tools use temporary
  profiles and keep raw logs outside the repository.
- If real Firefox geolocation remains unreliable, use Chrome as the supported
  browser, per the user's fallback decision. Do not switch support policy until
  this investigation is resolved.

### Remaining candidate fixes
- [ ] Guard animation: pause `requestAnimationFrame` when the tab is hidden
      (`visibilitychange`) and throttle scrub updates.
- [ ] Defer non-critical work (place lookup, candidate rendering) with
      `requestIdleCallback` where supported.
- [x] Remove Tailwind and its runtime CDN script; use self-contained native CSS
      for the responsive shell, route cards, search results, trip summaries, and controls.
- [ ] Add a Firefox-specific smoke test in CI (headless Firefox via Playwright).

### Acceptance criteria
- No UI lock for more than 2s on Firefox (Linux) with GeoClue disabled.
- "My Location" either succeeds or offers the map-tap fallback.
- Animation runs at >= 30fps on a mid-range laptop.

## Travel modes (planned)
- [ ] Add travel-mode selector: **walk**, **car**, **motorcycle**, **PUJ** (default: PUJ).
- [ ] Route walks/rides per mode (OSRM profiles: foot, driving, cycling/bike).
- [ ] Show mode-appropriate fares/costs and travel time.
- [ ] Keep PUJ as the primary, verified mode.

## General
- [ ] Investigate bounding the map to Davao City's boundaries, including how
      panning and zooming should behave. Record the approach before implementation.
- [ ] Persist Google Places key handling docs (already localStorage-only).
- [ ] Add offline-capable tile/cache strategy (optional).
- [ ] Improve walk routing (user-editable or Google Directions integration).
