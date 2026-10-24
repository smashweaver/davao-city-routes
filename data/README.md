# Route data acquisition

Research checkpoint: **October 24, 2026**. The application still contains five
selected prototype route records. This directory tracks evidence for expanding
coverage; its inventory is not loaded by the app.

## What was acquired

[`route-inventory.csv`](route-inventory.csv) contains **131 source entries**:

- 52 route features inspected in Commute Davao's publicly served JavaScript.
- 79 route-directory links counted in CommuteTour's Davao Jeep Quick Links.

These are source entries, not 131 distinct routes. Names overlap between sources;
aliases, variants, loops, and current service identities need reconciliation.
Neither source has been established as a complete inventory of active services.
The scope starts with Davao City jeepneys; source entries such as Panabo still
need classification as city or cross-boundary services. Bus evidence and the
official DC Bus stop-list acquisition are recorded below and in `ROADMAP.md`.

The CSV preserves each source's spelling, including `Calalunan Grande` in the
CommuteTour directory. `related_app_record` indicates a name-level relationship
only, never a verified geometry or service match. Blank coordinate counts and
closure values mean they were not audited. `source_checked_on` records when the
source was inspected, not when anyone verified a jeepney operation.

## Historical jeepney franchise master inventory

The [ADB December 2013 final report](https://www.adb.org/projects/documents/phi-davao-sustainable-urban-transport-project-final-report-dec-2013-tacr)
contains a substantially broader LTFRB-derived inventory: Part D, Review of
Existing Public Transport (June 2013), Annex A, printed pages 39–42. The report
identifies the underlying franchise records as **December 31, 2012**.

[`jeepney-franchise-inventory-2012.csv`](jeepney-franchise-inventory-2012.csv)
preserves **131 route entries plus eight AIRCON subrows**. The subrows retain
their parent route and are not counted as additional base routes. The extracted
counts sum exactly to the annex totals: **6,724 franchises and 7,278 units**.
This is separate from `route-inventory.csv`, whose 131 rows are overlapping
entries from two community catalogs; the matching counts are coincidental.

The [official PDF](https://www.adb.org/sites/default/files/project-document/172847/45296-003-tacr-01.pdf)
and document landing page returned HTTP 403/unavailable during this audit. The
annex was transcribed from the [public text mirror](https://www.scribd.com/document/947031506/45296-003-tacr-01).
The ADB-indexed document listing establishes the report title/date; PDF visual
verification of the table remains open. No subscription or restricted download
was used. [`Metadata`](jeepney-franchise-inventory-2012.metadata.json) records
provenance, the CSV SHA-256, totals, and limitations.

Each row retains the printed route name, historical franchise/unit counts,
printed page, source reference, and any circulation-route note. Wrapped names
were rejoined; original spelling and vehicle-mix text were preserved. Missing
vehicle-mix values were not filled or interpreted. `source_line` identifies the
line in the web tool's checked mirror snapshot, not a PDF page coordinate.

These are historical franchise records, not 131 services verified active in
2026. The table itself includes three base entries with zero units: Circulation
Route 14, Deca–Tacunan, and Ulas–Ulas loop. It contains no full alignment geometry,
ordered boarding stops, current schedules, or current fares. Do not import it
directly into trip planning.

Checks actually run: CSV parse, 139 rows with 131 unique base-route names and
eight attached AIRCON subrows, and both count totals reconciled against the
printed annex. A more recent official full route inventory was not located in
this search. The current-data request remains open; this historical list is a
reconciliation baseline, not the present-day coverage denominator.

## Sources and limits

| Source | Evidence acquired | Limits |
| --- | --- | --- |
| [Commute Davao](https://commutedavao.com/) | 52 named LineString features, 33,457 coordinate points; properties are only `name` and `color` | No explicit direction, stops, service hours, fares, current operating status, or validation dates in the extracted collection. Reuse permission/license not established in this audit. |
| [CommuteTour directory](https://ph.commutetour.com/travel/transport/jeep/davao-city-jeep-route-code/) | 79 route links in Davao Jeep Quick Links, including named and numbered variants | Directory page reports January 18, 2026 update; that does not date-check each operation. Individual route pages and geometries were not audited here. |
| [ADB final report, December 2013](https://www.adb.org/projects/documents/phi-davao-sustainable-urban-transport-project-final-report-dec-2013-tacr) | Historical LTFRB-derived Annex A transcribed to a separate CSV: 131 base route entries plus eight AIRCON subrows; counts reconcile | Data as of December 31, 2012; text mirror used because official download returned 403. Current service, geometry, and stops unverified. |
| [Davao Ordinance 108-00](https://lissp2.davaocity.gov.ph/uploads/items/25656/Ordinance%20No.%20000108-00.pdf) | Downloaded 38-page rerouting document; visually confirmed first page identifies Ordinance 108, series of 2000 | Historical baseline, not evidence that every listed service runs today. Scanned PDF; `pdftotext` produced no usable text. Full visual transcription remains open. |
| [LTFRB eFOI route request, 2020](https://www.foi.gov.ph/requests/davao-city-jeepney-routes/) | Read agency response directing the requester to a formal signed request | The public page is marked successful but contains no downloadable route dataset. Its instructions were directed to that requester and may have changed. |
| [LTFRB eFOI routes and fares request, 2021](https://www.foi.gov.ph/requests/davao-city-jeepney-routes-and-fare/) | Search result identifies a referral to Region XI | Direct page fetch failed; confirm current submission requirements with the agency. |
| [Official DC Bus routes page](https://davaobus.davaocity.gov.ph/dibs/public/bus/info) | Acquired 18 AM/PM stop-list records across nine route codes through the same public `ROUTES` request the page makes | Names and order only; no coordinates, route geometry, per-stop times, fares, or service validity dates in this response. Saved separately; not imported into the planner. |

The Commute Davao collection was extracted from the object assigned to `xy` in:

`https://commutedavao.com/main.021f6f2be17f97c4.js`

The object was parsed as data after quoting its identifier keys; the downloaded
application bundle was not executed. No other app code or configuration was
copied into this repository.

Audit artifacts are under `/tmp/davao-data-audit/`:

- `commutedavao-candidate.geojson`: extracted research geometry, using GeoJSON
  **longitude, latitude** order. The app uses the opposite order.
- `commutedavao.html` and `commutedavao-main.js`: downloaded public source.
- `ordinance.pdf`: historical official document.
- `jeepney-guide-tree.json`: inspected public repository inventory; no route
  dataset was identified in that tree.

Temporary files may disappear. Their location is a research checkpoint, not an
application dependency or a promise of durable storage. Source routes have not
been imported into `index.html`.

| Artifact | SHA-256 |
| --- | --- |
| Public JavaScript bundle | `d82e21e25ebf276cb9ed3197a0de284558bf324eb925b6d805d9f9a29e90ca30` |
| Extracted GeoJSON | `a7aeb0254238baaa703d58696396eb40f802286a36d7841fa096523343fd5bba` |

Checks actually run: JSON parsing; 52 features with unique names; all geometries
are LineStrings; all 33,457 coordinate pairs are finite and within valid global
longitude/latitude ranges. Bounds are longitude 125.454924–125.664695 and latitude
7.011324–7.267154. **43 paths have identical first and last coordinates.** Closure
does not establish loop service or identify an outbound/return split. Geometry
continuity, street access, service directions, and real operations remain
unverified. Browser regressions were not rerun for this data/documentation audit.

## What complete planning data must contain

Use a dated master inventory to establish the denominator for coverage. For each
service, acquire:

- Official identifier, public names/aliases, mode, operator, terminals, and variant.
- Current operating status, distinguishing authorized service from service
  actually observed running; preserve inactive records and their dates.
- Ordered outbound and return street alignments and geometries, or explicit
  loop direction. Never infer a return route by reversing an outbound line.
- Permitted boarding/alighting locations or rules, road side, restrictions,
  transfer locations, and pedestrian access/crossings where verified.
- Operating days/hours and either a schedule, frequency, or an explicit unknown
  value; last observation date for service availability.
- Current fare matrix/rules, fare-order reference, and effective date.
- Source URL/document, source date, field-validation date, confidence/status,
  and terms permitting reuse and public display.

Do not manufacture missing stops, directions, hours, or services from a driving
router. The current planner assumes bidirectional travel between consecutive
stops. Directional or loop geometries require a corresponding planner change
before import.

## Bus acquisition checkpoint

[`dc-bus-route-stops.json`](dc-bus-route-stops.json) preserves the official DC Bus
response with provenance, request details, and its raw-response SHA-256. The
request is a read-only route lookup: POST to
`https://davaobus.davaocity.gov.ph/dibs/application/api/app` with form field
`trans=ROUTES`, as used by the official public routes page.

The response contains **18 route/shift records across nine route codes**, with
**451 stop entries** and 96 distinct exact stop-name strings. Source order and
consecutive duplicate stops are preserved. Distinct strings do not establish
distinct physical locations. AM and PM identify service shifts; they are not
confirmed direction identifiers. Stop lists differ between shifts, so neither
list should be manufactured by reversing the other.

| DC Bus code | Published corridor title (AM record) |
| --- | --- |
| R102 | Toril - GE Torres |
| R103 | Toril - Roxas |
| R402 | Mintal - GE Torres |
| R403 | Mintal - Roxas |
| R503 | Bangkal - Roxas |
| R603 | Buhangin - Roxas |
| R763 | Panacan (via Buhangin) - Roxas |
| R783 | Panacan (via Angliongto) - Roxas |
| R793 | Panacan (via R Castillo) - Roxas |

The [official tracker landing page](https://davaobus.davaocity.gov.ph/dibs/)
publishes a regular Monday–Saturday schedule of 06:00–10:00 and 16:00–21:00,
with Sunday offline. This describes the published general service window,
not a timetable, guaranteed frequency, or confirmation that each bus is running.
The [city's September 4, 2026 announcement](https://davaocity.gov.ph/local-government/dc-bus-live-tracker-now-open-to-dabawenyos/)
identifies the tracker as a public city service.

Love Bus acquisition must remain separate from DC Bus even where corridor names
overlap:

| Love Bus corridor | Dated evidence | Remaining acquisition |
| --- | --- | --- |
| UM Matina–Tugbok | [PIA, September 24, 2026](https://pia.gov.ph/news/mindanao/dr/love-bus-davao-to-add-new-routes) reports operation | Official street alignment, designated stops, service calendar, and current operator/availability |
| Lasang–Sasa via Roxas | Same September 24 PIA report | Official street alignment, designated stops, service calendar, and current operator/availability |
| Toril–Roxas | September 24 PIA report announced it; [GMA Regional TV, October 1, 2026](https://www.gmanetwork.com/regionaltv/onemindanao/159762/dugang-ruta-nga-toril-downtown-davao-city-sa-love-bus---libreng-sakay-i-one-mindanao/video/) reports service launch | Current official route order, geometry, stop list, and service calendar; the PIA announcement described 06:00–09:00 and 17:00–20:00 free rides |

The broader [Davao Public Transport Modernization Project](https://www.adb.org/projects/45296-006/main)
is a separate planned network. Planned alignments can be recorded as planned,
but require a dated operating-service confirmation before journey eligibility.
Do not use project target dates to activate a route automatically.

Bus integration needs designated-stop boarding, directional geometry, calendar
and time-window checks, transfer rules, and dated fare/free-ride rules. A nearby
point on a bus polyline is insufficient evidence of a permitted boarding stop.
The official response acquired here still needs stop coordinates, authoritative
geometry, calendars, and reuse terms before planner import. The public map page
was inspected only to identify its loading script; no map geometry was acquired.

Checks actually run for this acquisition: response parsed as JSON; 18 unique
record IDs; nine route codes each with AM and PM records; 451 nonempty stop-name
entries; no coordinate or timing fields silently inferred. Raw HTTP artifacts
remain in `/tmp/davao-data-audit/` with the other research downloads.

## Official-data request draft

For the current jeepney master list, use the dedicated
[submission steps and copyable eFOI letter](LTFRB-REQUEST.md). The broader draft
below also covers bus services, geometry, stops, and schedules.

Prepared for the user to review and submit through the current official channel;
**nothing has been sent**. Confirm contact details and requirements directly
with LTFRB Region XI. CTTMO can be approached for city rerouting and boarding
restrictions, and operators can help verify actual service.

**Subject: Request for current Davao City jeepney and bus route master lists and GIS data for a commuter application**

Dear LTFRB Region XI,

I am evaluating a commuter-planning prototype for Davao City and would like to request
the latest available inventory of public utility jeepney, filcab, and city bus
services within Davao City, including cross-boundary services that pick up or
drop off passengers within the city. Please include Love Bus, PHABS, and DC Bus
where maintained by your office, and distinguish the planned DPTMP network from
operating services. Please identify the inventory's coverage and effective/as-of
date. If DC Bus information is maintained by the city/DIBS office, please advise
the appropriate referral; its published route/stop-name lists have already been
located, and stop coordinates, geometry, and operating calendars are still needed.

Where available, please provide:

1. Route identifiers/names, aliases, variants, terminals, operators, authorized
   units, and operational units or other evidence of current service. Please
   distinguish active, suspended, discontinued, and planned routes.
2. Separate outbound/return alignments or loop directions, ordered streets,
   rerouting orders, and GIS geometry in GeoJSON, KML, shapefile, or GTFS format.
3. Designated boarding/alighting points and relevant restrictions, including
   road side and no-loading/unloading areas where recorded.
4. Operating days/hours, schedules or frequencies where recorded, and current
   fare matrices/orders with their effective dates.
5. Metadata describing completeness, last update, and permission/attribution
   requirements for use and public display in a research prototype.

CSV/XLSX route tables and scanned route documents would also be helpful where
machine-readable GIS data is unavailable. Please identify unavailable fields and
the office or contact that maintains them. Please also advise how route changes
can be obtained for ongoing maintenance.

This request concerns routes and services; personal driver/passenger information
is not requested. I can provide the signed request and supporting information
required by your current process.

Thank you.

[Name]
[Contact details]

## Next acquisition steps

1. Obtain the dated official master inventory and establish reuse terms for
   candidate geometry before publishing an imported dataset.
2. Reconcile the 52-feature collection, 79 directory entries, official inventory,
   and existing five app records without automatically merging similar names.
3. Validate route direction and actual service with operators/local observations;
   keep unresolved conflicts explicit.
4. Correct the planner's directional model, then import validated services with
   provenance and verify representative commutes and regressions.

Current gap: a verified current master inventory and permission to reuse the
candidate geometry have not been acquired. No complete, current, verified public
feed was established by this search.
