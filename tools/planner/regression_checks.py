"""Browser regressions for direct walks and route-road access; fixtures are approximate."""

import argparse
import asyncio
import math
from urllib.parse import urlsplit

from playwright.async_api import async_playwright


async def check(browser_type, url):
    browser = await browser_type.launch(**({'channel': 'chrome'} if browser_type.name == 'chromium' else {}))
    try:
        context = await browser.new_context()
        await context.route('**/*.tile.openstreetmap.org/**', lambda route: route.abort())
        walk_requests = []

        async def walking_route(route):
            walk_requests.append(route.request.url)
            await route.fulfill(status=503, body='Use straight walking fallback')

        await context.route('**/router.project-osrm.org/**', walking_route)
        page = await context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_function("typeof map !== 'undefined' && map && davaoRoutes.every(route => route.stopInfo)")

        # Both points are north of the same stop: walking via that stop would
        # add almost 2 km to an approximately 103 m direct walk.
        result = await page.evaluate('''() => {
          const stop = landmarks['matina-crossing'];
          const origin = {lat: stop.coords[0] + 997 / 111195, lng: stop.coords[1], label: 'Test origin'};
          const destination = {lat: stop.coords[0] + 1100 / 111195, lng: stop.coords[1], label: 'Savemore'};
          const trip = buildTrip({edges: [], originStop: {key:'matina-crossing',distance:997},
            destinationStop:{key:'matina-crossing',distance:1100}}, origin, destination);
          window.walkFixture = {origin, destination};
          return {legCount:trip.legs.length, distance:trip.totalWalk,
            from:trip.legs[0]?.from.label, to:trip.legs.at(-1)?.to.label, transfers:trip.transfers};
        }''')
        assert result['legCount'] == 1, f'Walking-only trip includes intermediate stops: {result}'
        assert 102 < result['distance'] < 104, result
        assert result['from'] == 'Test origin' and result['to'] == 'Savemore', result
        assert result['transfers'] == 0, result
        print('PASS: shared-stop walking trip goes directly to Savemore with recomputed distance', flush=True)

        # A graph walking edge must not become a compulsory intermediate stop.
        result = await page.evaluate('''() => {
          const edge = Object.values(buildTripGraph()).flat().find(edge => edge.type === 'walk');
          const a = landmarks[edge.from], b = landmarks[edge.to];
          const origin = {lat:a.coords[0]+0.0005,lng:a.coords[1],label:'Origin'};
          const destination = {lat:b.coords[0]+0.0005,lng:b.coords[1],label:'Destination'};
          const trip = buildTrip({edges:[edge],originStop:{key:edge.from,distance:56},
            destinationStop:{key:edge.to,distance:56}},origin,destination);
          return {legs:trip.legs.length,from:trip.legs[0].from,to:trip.legs[0].to,
            distance:trip.totalWalk,expected:haversineDistance([origin.lat,origin.lng],[destination.lat,destination.lng])};
        }''')
        assert result['legs'] == 1 and result['from']['label'] == 'Origin' and result['to']['label'] == 'Destination', result
        assert abs(result['distance'] - result['expected']) < 0.01, result
        print('PASS: walking-only graph paths use the actual origin and destination', flush=True)

        # Check the full planner, rendered instructions, and requested walking
        # geometry rather than merely changing the displayed destination label.
        walk_requests.clear()
        await page.evaluate('planTrip(walkFixture.origin, walkFixture.destination)')
        await page.wait_for_selector('.trip-legs')
        assert await page.locator('.trip-leg').count() == 1
        assert 'Savemore' in await page.locator('.trip-leg').inner_text()
        assert 'Matina Crossing' not in await page.locator('.trip-legs').inner_text()
        endpoints = await page.evaluate('`${walkFixture.origin.lng},${walkFixture.origin.lat};${walkFixture.destination.lng},${walkFixture.destination.lat}`')
        assert len(walk_requests) == 1 and endpoints in walk_requests[0], walk_requests
        print('PASS: planner renders one walk and requests geometry between the actual endpoints', flush=True)

        # A real jeepney journey still keeps rides and access/egress walking.
        result = await page.evaluate('''() => {
          const route = davaoRoutes.find(route=>route.id==='toril');
          const from='matina-crossing',to='ulas',a=landmarks[from],b=landmarks[to];
          const start=route.stopInfo[from].progress,end=route.stopInfo[to].progress;
          const distance=Math.abs(end-start)*route.cumulative.at(-1);
          const origin={lat:a.coords[0]+0.0005,lng:a.coords[1],label:'Origin'};
          const destination={lat:b.coords[0]+0.0005,lng:b.coords[1],label:'Destination'};
          return buildTrip({edges:[{type:'ride',route,from,to,fromProgress:start,toProgress:end,distance}],
            originStop:{key:from,distance:56},destinationStop:{key:to,distance:56}},origin,destination).legs.map(leg=>leg.type);
        }''')
        assert result == ['walk', 'ride', 'walk'], result
        await page.locator('#chat-input').fill('from Matina to Abreeza')
        await page.locator('#search-btn').click()
        await page.wait_for_function("currentTrip && currentTrip.destination.key === 'abreeza'")
        assert await page.evaluate("currentTrip.legs.some(leg => leg.type === 'ride')")
        assert not errors, errors
        print('PASS: jeepney journeys retain their ride and access/egress walking legs', flush=True)

        # The journey result is the single source for lines, markers, and steps:
        # ordered waypoints, connected legs, and a board/get-off marker per ride.
        result = await page.evaluate('''() => {
          const journey = currentJourney;
          const ids = new Set(journey.waypoints.map(w => w.id));
          const connected = journey.legs.every(leg => ids.has(leg.fromId) && ids.has(leg.toId));
          const endpoints = journey.legs.every(leg => {
            const get = id => journey.waypoints.find(w => w.id === id);
            const from = get(leg.fromId), to = get(leg.toId);
            const start = leg.path[0], end = leg.path[leg.path.length - 1];
            return from.lat === start[0] && from.lng === start[1] && to.lat === end[0] && to.lng === end[1];
          });
          const tagged = journey.waypoints.filter(w => w.type === 'board' || w.type === 'alight').length;
          return {first: journey.waypoints[0].type, last: journey.waypoints.at(-1).type,
            rides: journey.legs.filter(l => l.type === 'ride').length, connected, endpoints, tagged};
        }''')
        assert result['first'] == 'origin' and result['last'] == 'destination', result
        assert result['rides'] >= 1 and result['connected'] and result['endpoints'], result
        assert await page.locator('.journey-badge.is-board').count() >= 1
        assert await page.locator('.journey-badge.is-alight').count() >= 1
        print('PASS: journey result exposes ordered waypoints, connected walk/ride legs, and board/get-off markers', flush=True)

        # A shared transfer point is marked once and names both services.
        await page.locator('#chat-input').fill('from Calinan to SM Lanang')
        await page.locator('#search-btn').click()
        await page.wait_for_function("currentJourney && currentJourney.destination.key === 'sm-lanang'")
        result = await page.evaluate('''() => {
          const journey = currentJourney;
          const transfers = journey.waypoints.filter(w => w.type === 'transfer');
          return {transfers: transfers.length, rides: journey.legs.filter(l => l.type === 'ride').length,
            transferRoutes: transfers.map(w => w.routeIds.length)};
        }''')
        assert result['rides'] == 2 and result['transfers'] == 1, result
        assert result['transferRoutes'] == [2], result
        assert await page.locator('.journey-badge.is-transfer').count() == 1
        assert await page.locator('.journey-badge.is-alight').count() == 1
        print('PASS: a shared transfer is marked once and names both services', flush=True)

        # Approximate Flores Village area, not the user's stored location or a
        # claim about a designated stop. The nearby road is on Toril/Mintal lines.
        result = await page.evaluate('''async () => {
          const origin = {lat:7.05748,lng:125.55946,label:'Flores area test'};
          const destination = {key:'sm-lanang',lat:landmarks['sm-lanang'].coords[0],
            lng:landmarks['sm-lanang'].coords[1],label:'SM Lanang'};
          const before = JSON.stringify(buildTripGraph());
          await planTrip(origin,destination);
          const trip = currentTrip;
          const ride = trip.legs.find(leg => leg.type === 'ride');
          const stop = trip.stops[ride.fromStop];
          const expected = interpolatePath(ride.route.coordinates,ride.route.cumulative,ride.fromProgress);
          window.accessFixture = {origin,destination};
          return {walk:trip.legs[0].distance,firstType:trip.legs[0].type,
            estimated:stop.estimated,stopError:haversineDistance(stop.coords,expected),
            to:trip.legs[0].to.label,baseUnchanged:before===JSON.stringify(buildTripGraph()),
            globalUnchanged:!Object.keys(landmarks).some(key=>key.startsWith('access-'))};
        }''')
        assert result['firstType'] == 'walk' and result['walk'] < 600, result
        assert result['estimated'] and result['stopError'] < 0.01, result
        assert 'Matina Crossing' not in result['to'], result
        assert result['baseUnchanged'] and result['globalUnchanged'], result
        assert 'access is estimated' in await page.locator('.assistant-card').inner_text()
        print('PASS: Flores-area trip boards on a nearby served road instead of walking to Matina', flush=True)
        print(f"  Approximate Flores fixture: {result['walk']:.0f} m initial walk; endpoint on route line", flush=True)

        # Test both directions, including boarding between the same two landmarks.
        result = await page.evaluate('''() => {
          const a={lat:7.06135,lng:125.55962,label:'Road A'};
          const b={lat:7.06003,lng:125.55190,label:'Road B'};
          const graph=buildAccessGraph(a,b);
          const path=shortestPath(graph.adjacency,'access-0-toril','access-1-toril');
          const reverse=shortestPath(graph.adjacency,'access-1-toril','access-0-toril');
          const back=findTrip(accessFixture.destination,accessFixture.origin);
          const last=back.legs.at(-1);
          return {path:path?.edges.map(e=>e.type),reverse:reverse?.edges.map(e=>e.type),
            distance:path?.edges.reduce((sum,e)=>sum+e.distance,0),
            reverseDistance:reverse?.edges.reduce((sum,e)=>sum+e.distance,0),
            finalType:last.type,finalDistance:last.distance,finalLabel:last.to.label};
        }''')
        assert result['path'] == ['ride'] and result['reverse'] == ['ride'], result
        assert abs(result['distance'] - result['reverseDistance']) < 0.01, result
        assert result['finalType'] == 'walk' and result['finalDistance'] < 600, result
        assert result['finalLabel'] == 'Flores area test', result
        print('PASS: access points split route edges in both directions and support nearby alighting', flush=True)

        result = await page.evaluate('''() => {
          const origin={lat:7.05748,lng:125.55946,label:'Origin'};
          const destination={lat:7.05798,lng:125.55946,label:'Nearby shop'};
          const close=findTrip(origin,destination);
          const far=findTrip({lat:8,lng:126,label:'Outside'},accessFixture.destination);
          return {legs:close.legs.map(leg=>leg.type),distance:close.totalWalk,far};
        }''')
        assert result['legs'] == ['walk'] and 55 < result['distance'] < 57, result
        assert result['far'] is None, result
        assert not errors, errors
        print('PASS: direct walking competes with transit and distant origins stay unsupported', flush=True)

        # Coordinate input bypasses place search and preserves numeric precision.
        geocode_requests = []

        async def unexpected_geocode(route):
            geocode_requests.append(route.request.url)
            await route.fulfill(status=503, body='Coordinate lookup should stay local')

        await context.route('**/nominatim.openstreetmap.org/**', unexpected_geocode)
        await context.route('**/places.googleapis.com/**', unexpected_geocode)
        coordinate_text = '7.091450123456, 125.610330123456'
        result = await page.evaluate('''text => {
          const bare=parseTripQuery(text);
          const origin=parseTripQuery(`from ${text} to SM Lanang`);
          const signed=parseTripQuery('from -7.25, +125.50 to +7.75, -125.25');
          const chat=parseTripQuery("I'm at Matina, going to Abreeza");
          return {bare:bare.destination,origin:origin.origin,to:origin.destination.key,
            signedOrigin:signed.origin,signedDestination:signed.destination,
            chat:[chat.origin.key,chat.destination.key],
            invalid:parseTripQuery('91, 125').error,
            invalidOrigin:parseTripQuery('from 7, 181 to Abreeza').error};
        }''', coordinate_text)
        assert result['bare']['lat'] == 7.091450123456 and result['bare']['lng'] == 125.610330123456, result
        assert result['origin'] == result['bare'] and result['to'] == 'sm-lanang', result
        assert result['signedOrigin']['lat'] == -7.25 and result['signedOrigin']['lng'] == 125.5, result
        assert result['signedDestination']['lat'] == 7.75 and result['signedDestination']['lng'] == -125.25, result
        assert result['chat'] == ['matina-crossing', 'abreeza'], result
        assert result['invalid'] and result['invalidOrigin'], result

        await page.evaluate("userLocation = {lat:7.07252,lng:125.61220,label:'Test origin'}")
        await page.locator('#chat-input').fill(coordinate_text)
        await page.locator('#search-btn').click()
        await page.wait_for_function('currentTrip.destination.lat === 7.091450123456')
        await page.wait_for_selector('.trip-title:has-text("7.091450")')
        # Both coordinate places have a null key; that must not mean same place.
        await page.locator('#chat-input').fill(f'from {coordinate_text} to 7.09897, 125.63077')
        await page.locator('#search-btn').click()
        await page.wait_for_function('currentTrip.origin.lat === 7.091450123456 && currentTrip.destination.lat === 7.09897')
        await page.wait_for_selector('.trip-title:has-text("7.098970")')
        await page.locator('#chat-input').fill('from 91, 125 to Abreeza')
        await page.locator('#search-btn').click()
        await page.wait_for_selector('.assistant-card:has-text("latitude must be between")')
        assert not geocode_requests, geocode_requests
        assert not errors, errors
        print('PASS: pasted coordinates work as destinations and origins without place lookup; invalid ranges are explained', flush=True)

        # A nearby destination can require a long road detour. Use approximate
        # neighborhood fixtures, rather than recording exact device coordinates.
        await context.unroute('**/router.project-osrm.org/**', walking_route)
        road_requests = []
        origin = [125.5601, 7.0558]
        destination = [125.5688, 7.0453]

        async def detour_route(route):
            road_requests.append(route.request.url)
            parts = urlsplit(route.request.url).path.rsplit('/', 1)[1].split(';')
            start, end = [[float(n) for n in point.split(',')] for point in parts]
            a, b = math.radians(start[1]), math.radians(end[1])
            delta_lat, delta_lng = b-a, math.radians(end[0]-start[0])
            straight = 6371000 * 2 * math.asin(math.sqrt(math.sin(delta_lat/2)**2 +
                math.cos(a)*math.cos(b)*math.sin(delta_lng/2)**2))
            distance = 3600 if start == origin and end == destination else straight * 1.25
            await route.fulfill(json={'code':'Ok','routes':[{'distance':distance,
                'geometry':{'coordinates':[start,end]}}]})

        await context.route('**/router.project-osrm.org/**', detour_route)
        result = await page.evaluate('''async () => {
          walkPathCache.clear();
          const origin={lat:7.0558,lng:125.5601,label:'Neighborhood origin'};
          const destination={lat:7.0453,lng:125.5688,label:'Neighborhood destination'};
          const before=findTrip(origin,destination).legs.map(leg=>leg.type);
          await planTrip(origin,destination);
          window.detourFixture={origin,destination};
          return {before,types:currentTrip.legs.map(leg=>leg.type),walk:currentTrip.totalWalk,
            firstWalk:currentTrip.legs[0].distance,to:currentTrip.legs[0].to.label,
            routes:currentTrip.legs.filter(leg=>leg.type==='ride').map(leg=>leg.route.id),
            estimated:currentTrip.estimatedWalking};
        }''')
        assert result['before'] == ['walk'], result
        assert result['types'] == ['walk','ride','walk'], result
        assert result['routes'][0] in ['toril','mintal'], result
        assert 700 < result['firstWalk'] < 850 and result['walk'] < 3000, result
        assert 'nearby road' in result['to'] and not result['estimated'], result
        assert len(road_requests) <= 7 and len(road_requests) == len(set(road_requests)), road_requests
        assert 'Direct jeepney ride' in await page.locator('.trip-summary').first.inner_text()
        print('PASS: a long road detour changes the winner from walking to walk–jeep–walk; shared path requests are deduplicated', flush=True)

        # Keep searching for a ride when a graph-only walking path is cheaper;
        # charge the boarding penalty only for subsequent rides, even after a walk.
        result = await page.evaluate('''() => {
          const a=davaoRoutes[0],b=davaoRoutes[1];
          const graph={a:[{type:'walk',from:'a',to:'b',cost:100},
            {type:'ride',from:'a',to:'b',route:a,cost:200}],
            b:[{type:'ride',from:'b',to:'c',route:b,cost:300}]};
          return {walk:shortestPath(graph,'a','b').edges[0].type,
            ride:shortestPath(graph,'a','b',true).edges[0].type,
            first:shortestPath(graph,'a','b',true).cost,
            afterWalk:shortestPath(graph,'a','c',true).cost,
            twoRides:tripCost({legs:[{type:'ride',distance:200},{type:'ride',distance:300}],totalWalk:0}),
            expectedTransfer:500+BOARDING_PENALTY};
        }''')
        assert result['walk'] == 'walk' and result['ride'] == 'ride', result
        assert result['first'] == 200 and result['afterWalk'] == 400, result
        assert result['twoRides'] == result['expectedTransfer'], result

        # A pending routing response must not replace a newer starting point.
        await context.unroute('**/router.project-osrm.org/**', detour_route)
        release = asyncio.Event()
        started = asyncio.Event()

        async def delayed_route(route):
            started.set()
            await release.wait()
            await route.fulfill(status=503, body='Delayed road lookup failure')

        await context.route('**/router.project-osrm.org/**', delayed_route)
        await page.evaluate('''() => {
          walkPathCache.clear();
          window.oldPlan=planTrip(detourFixture.origin,detourFixture.destination);
        }''')
        await asyncio.wait_for(started.wait(), timeout=5)
        await page.locator('#chat-input').fill("I'm at Abreeza")
        await page.locator('#search-btn').click()
        release.set()
        await page.evaluate('oldPlan')
        assert 'Starting point set to' in await page.locator('.assistant-card').inner_text()
        assert await page.evaluate('userLocation.key') == 'abreeza'
        await context.unroute('**/router.project-osrm.org/**', delayed_route)

        await context.route('**/router.project-osrm.org/**', walking_route)
        await page.evaluate('''async () => {
          walkPathCache.clear();
          await planTrip(detourFixture.origin,detourFixture.destination);
        }''')
        assert await page.evaluate('currentTrip.estimatedWalking')
        assert 'straight-line estimates' in await page.locator('.assistant-card').inner_text()
        assert not errors, errors
        print('PASS: first rides avoid a transfer penalty; unavailable routing is labeled and stale plans cannot replace newer input', flush=True)
    finally:
        await browser.close()


async def main(args):
    async with async_playwright() as playwright:
        for name in args.browsers:
            print(f'Checking {name}', flush=True)
            await check(getattr(playwright, name), args.url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000/')
    parser.add_argument('--browsers', nargs='+', choices=['firefox', 'chromium'], default=['firefox', 'chromium'])
    asyncio.run(main(parser.parse_args()))
