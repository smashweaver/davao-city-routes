# Roadmap — Davao Jeep Routes

## Product direction

This project is an exploratory spike for Davao commute planning. Its purpose is
to test the experience, understand the route-data gaps, and preserve findings
for later work.

- **Current stage:** validate route exploration, commute planning, automatic
  location, and the experience on desktop and mobile.
- **Immediate scope:** preserve the existing app while collecting route evidence
  and preparing bus-route integration. Broader app changes are deferred.
- **Longer-term possibility:** once the road and transit-route network is
  complete and validated, explore connecting it to traffic monitoring.

### Product inspiration

The inspiration is a Singapore transit app that brings bus and train routes
around the city into one place. Its name has not yet been recorded.

Use that experience as a reference for making Davao's transport network easy to
explore and journeys easy to plan. The current spike starts with local jeepney
routes; use the Singapore reference to guide the route map, search, and journey
planning experience as the spike is evaluated.

### Validation milestones

- [ ] Establish reliable real-device location and decide which browsers to support.
- [ ] Validate route information and trip results with real commute examples.
- [ ] Validate the mobile experience for everyday use.
- [ ] Complete and validate the road and transit-route network as a foundation
      for later work.

### Longer-term traffic monitoring

A completed road and transit-route network could provide a foundation for
traffic monitoring and eventually help relate observed traffic conditions to
commute planning. This is a future investigation. Traffic-data sources,
availability, update frequency, and integration have not been established, and
implementation is outside the current spike scope.

### Route data completeness

Current scope, confirmed October 24, 2026: preserve the app while collecting
route evidence. Bus-route integration is the only requested app expansion;
broader planner changes, walking preferences, and jeepney-data imports are
deferred. The investigations below do not authorize implementing those changes.

The October 24, 2026 [acquisition audit](data/README.md) found 52 route geometries
in Commute Davao's public web bundle (33,457 coordinate points) and 79 route
entries in CommuteTour's directory. The [source inventory](data/route-inventory.csv)
preserves 131 source entries, including overlap; it is not a distinct-service
count. Current operations, directions, stops, fares, hours, and reuse terms have
not been established for the candidate geometry. The app still has five selected
prototype routes. No complete current verified feed was established by the search.

- [x] Record candidate source inventories and inspect the 52-feature geometry
      collection without importing it into the planner.
- [x] Prepare an official-data request draft in the audit and dedicated
      [jeepney master-list submission steps and letter](data/LTFRB-REQUEST.md);
      no request sent.
- [x] Find and transcribe the historical LTFRB-derived jeepney franchise
      inventory in the ADB December 2013 report: 131 base route entries plus
      eight AIRCON subrows, data as of December 31, 2012. Historical counts
      reconcile to 6,724 franchises and 7,278 units. The official PDF returned
      HTTP 403; transcription uses a public text mirror, with provenance in
      [`data/jeepney-franchise-inventory-2012.metadata.json`](data/jeepney-franchise-inventory-2012.metadata.json).
      This is not a current active-service list or a planner import.
- [ ] Obtain a dated LTFRB Region XI master inventory, including active/inactive
      status and variants; acquire CTTMO rerouting/boarding restrictions.
- [ ] Establish reuse terms for candidate geometry and reconcile official,
      community, and existing app records, preserving unresolved differences.
- [ ] Acquire and validate separate outbound/return alignments or loop
      directions, boarding rules, operating hours, and fare references.
- [ ] Replace the planner's blanket bidirectional assumption before importing
      services whose directions differ; validate representative real commutes.
- [ ] Establish a dated coverage denominator and a process for service updates.

### Bus routes and free-ride services

- [x] Acquire official DC Bus AM/PM stop-name lists: 18 records across nine
      route codes and 451 stop entries, saved with provenance in
      [`data/dc-bus-route-stops.json`](data/dc-bus-route-stops.json). Stops are
      names only; coordinates, geometry, per-stop times, fare rules, and service
      validity dates are not present in this response. No planner import yet.
- [x] Record dated Love Bus evidence for UM Matina–Tugbok, Lasang–Sasa via
      Roxas, and the Toril–Roxas launch reported October 1, 2026; keep these
      distinct from DC Bus and the planned DPTMP network in the acquisition audit.
- [ ] Identify and map **Love Bus** and **Davao City Bus / DC Bus (Davao City
      Interim Bus Service)** routes alongside jeepney routes.
- [ ] Obtain and verify official boarding/alighting stop coordinates,
      directional geometry, operating days and time windows, transfer
      restrictions, and current fare/free-ride rules for each service. Record
      sources and dates checked before planner integration; permit bus boarding
      only at verified designated stops.
- [ ] Investigate whether the free-ride services collect commuter feedback to
      refine routes. This is a user hypothesis to verify, not an established
      explanation for the free rides.
- [ ] Plan how bus and jeepney options, transfers, and service availability will
      appear together in search and trip results.
- [ ] Keep proposed DPTMP routes in planned status until a dated operational
      confirmation supports including them in journey search.

Research starting points: the [official Davao Bus portal](https://davaobus.davaocity.gov.ph/)
links to live DC Bus locations and route information. A
[March 18, 2026 Philippine Information Agency report](https://pia.gov.ph/news/buses-offering-free-rides-continue-serving-davao-city/)
documents free rides on both Love Bus and DC Bus; recheck current operations
before treating routes, schedules, or free fares as app data.

## Firefox freezing (priority)

Symptom: page can lock up in Firefox (Linux), especially around geolocation and
map rendering. Requesting location has triggered the freeze both before and
after installing GeoClue; the underlying browser/OS cause is still unconfirmed.

### Status

- [x] Trigger identified: requesting browser geolocation on Linux Firefox has
      reproduced the freeze. Installing GeoClue did not resolve the report.
- [x] Identified the missing GeoClue permission agent during investigation;
      restored client creation temporarily. GeoClue was later removed at the
      user's request; real-location reliability remains unresolved.
- [x] Replaced the temporary Firefox map-only workaround with an automatic
      location watch that accepts fixes reporting accuracy of 500 m or better,
      cancels after success, and falls back after 12 seconds.
- [ ] Establish repeated real-location reliability before closing the Firefox
      issue; a JavaScript timer cannot recover a hung browser process.

### Native geolocation investigation — October 24, 2026

- Test environment at the time: Firefox 158.0.1 on Pop!_OS 24.04 / COSMIC;
  GeoClue 2.7.0 before its subsequent removal.
- Confirmed blocker: the GeoClue desktop permission agent was absent from the
  running session. A direct D-Bus `Manager.GetClient` call timed out independently
  of the app. GeoClue 2.7.0 queues client creation until an agent registers.
- Started `/usr/libexec/geoclue-2.0/demos/agent` under the transient user service
  `geoclue-demo-agent.service`. The same D-Bus call then succeeded in about 0.05s.
  `/etc/xdg/autostart/geoclue-demo-agent.desktop` existed at the time;
  no additional autostart file was needed during that investigation.
- GeoClue was subsequently purged from the development system at the user's
  request, including its configuration and autostart entry. The session agent
  was stopped. Firefox was configured to use its direct network provider;
  recheck profile settings before any further native-provider investigation.
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

## Search and map experience

- [x] Accept decimal latitude/longitude pairs directly in Find Route as a
      destination or an explicit origin, preserving precision and validating ranges.
- [x] Set the starting point by dropped pin or typed coordinates as well as
      automatic location; drag a dropped pin to move it and re-plan.
      `setOrigin()` owns the choice, `originSource` records how it was made, and
      the three options stay collapsed behind the status line so the panel keeps
      its height. Manual choices survive a later location fix.
- [x] Show a destination flag pin and permanent label, including while finding
      the starting point or when the current route network cannot connect a trip.

## Full-journey animation

Playback covers the complete journey through the walk/ride boundaries in the
journey result. Further boundary refinement remains open under route finding.

- [x] Return one organized journey result containing origin, destination,
      ordered tagged waypoints, and connecting walk/ride legs with geometry.
      `buildJourney()` now normalizes a planned trip into this result, and the
      map and instructions read it instead of re-deriving the boundaries.
- [x] Animate access walking, every jeep ride and transfer, and final walking
      to the destination in sequence, using the geometry of each trip leg.
- [x] Change the moving marker between walking and jeep representations at
      boarding/alighting points without jumps between disconnected paths.
- [x] Extend play/pause, speed, follow-camera, and the progress slider across
      the complete journey; preserve standalone route playback.
- [x] Verify walking-only, walk–ride–walk, and multi-ride journeys, including
      scrubbing across mode changes and reaching the destination.

Playback time is proportional to distance rather than leg type; toggling the
walk display restarts playback from the origin. See [README.md](README.md) for
the playback architecture and verification details.

## Boarding points and route finding

### Planner correctness: gray area for the next handover

User priority recorded October 24, 2026: verify that the planner finds the
shortest practical complete journey from the user's starting point to the
destination, including walking to a suitable boarding point and taking multiple
jeep rides when needed. The boarding choice must account for the onward trip.
This remains unresolved; existing examples do not prove optimal journeys.
The current objective is ride distance + 3 × walking distance + 4,200 per
additional boarding. It does not minimize distance alone or establish fastest
travel time. This investigation does not authorize planner behavior changes.

Code trace — October 25, 2026: `shortestPath()` returns one weighted path for
each origin/destination access-point pair. `findTripCandidates()` deduplicates
those paths, ranks them using straight-line walking estimates, and keeps at
most three ride itineraries. `planTrip()` then requests road paths for only
those retained candidates and re-ranks them. Road detours therefore cannot
rescue a route omitted by the initial shortlist, and another path for the same
access-point pair is never compared. The saved Calinan–SM Lanang regression
checks that a two-ride transfer is represented; it does not compare the result
with independently enumerated alternatives or establish optimality. This is a
source-level limitation, not yet a demonstrated wrong trip on a validated
route network.

Browser verification was attempted October 25, 2026 but could not run in this
environment: Playwright is absent from the available Python runtime and the
offline `uv` cache, the local server ports were not reachable, and the Firefox
DevTools MCP process exited while listing tabs. Syntax verification and
`git diff --check` passed; no planner behavior was exercised in this session.

- [ ] Define how commuters choose between least walking, lowest fare,
      shortest total distance, and fastest trip, including a walking limit and
      the effect of transfers. Some accept longer walks to save money; others
      minimize walking. Compare walking distance, estimated fare, and transfers
      for the available options.
- [ ] Establish validated fare rules for each ride and transfer before claiming
      savings from a longer walk. The current weighted score is not a peso
      cost and does not optimize fares; preference controls remain future work.
- [ ] Verify one-ride and multiple-ride journeys against independently reasoned
      expected results, including a nearby route that cannot connect onward,
      competing boarding points, road detours, and unsupported destinations.
- [ ] Audit whether sparse transfer points, access-point generation, and the
      three-itinerary shortlist can exclude a better complete journey.
- [ ] Record expected versus actual results and distinguish algorithm limits
      from incomplete route data, assumed directions, and unverified boarding.

### Existing progress and remaining work

- [x] Consider nearby points along mapped jeep route lines when choosing the
      initial boarding point, rather than requiring a walk to a named landmark.
- [x] Compare short direct walks with transit and remove landmark detours from
      walking-only trips.
- [x] Compare road distances for the direct walk and shortlisted jeep options
      before choosing a trip; apply the boarding penalty only to transfers.
- [ ] Investigate whether walking sections along mapped jeep routes could be
      ridden, and refine boarding/alighting boundaries where appropriate.
      Require sustained overlap within a tested tolerance, route identity, and
      valid direction; a single crossing is insufficient. Keep the default
      free of added dependencies; Turf.js is not required.
- [x] Show static BOARD and GET OFF markers for every ride, including a single
      jeep trip; retain dashed walking links and solid ride sections.
- [ ] Validate the Flores Village / Bangkal boarding location on the ground,
      including entrances, the correct side of the road, and permitted stops.
- [ ] Rank access points using actual pedestrian routes, accounting for gates,
      barriers, crossings, and walking detours before selecting a trip.
- [ ] Verify a pedestrian-routing provider; an OSRM URL containing `foot`
      does not establish which transport profile its server actually uses.
- [ ] Investigate user-editable walking paths or Google Directions integration
      as alternatives for improving walk routing.
- [ ] Add verified boarding/alighting stops and road names along route segments;
      distinguish designated bus stops from inferred jeepney road access.

## General

- [ ] Investigate bounding the map to Davao City's boundaries, including how
      panning and zooming should behave. Record the approach before implementation.
- [x] Document Google Places key storage, API setup, billing, and referrer
      restrictions in [README.md → Place lookup](README.md#place-lookup).
- [ ] Add offline-capable tile/cache strategy (optional).
