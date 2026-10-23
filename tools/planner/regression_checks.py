"""Browser regressions for direct walks and route-road access; fixtures are approximate."""

import argparse
import asyncio

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
