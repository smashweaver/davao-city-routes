import argparse
import asyncio
from playwright.async_api import async_playwright

MOCK='''() => {
 window.watches=[]; window.cleared=[];
 Object.defineProperty(navigator,'geolocation',{configurable:true,value:{
  watchPosition(success,error,options){const id=watches.length;watches.push({success,error,options});return id},
  clearWatch(id){cleared.push(id)}
 }});
 window.deliver=(id,accuracy,latitude=7.05871,longitude=125.56881)=>watches[id].success({coords:{latitude,longitude,accuracy}});
}'''

async def main(args):
 async with async_playwright() as p:
  for name in args.browsers:
   browser=await getattr(p,name).launch(**({'channel': 'chrome'} if name == 'chromium' else {}))
   async def setup(script=MOCK):
    c=await browser.new_context()
    await c.add_init_script(f'({script})();')
    await c.route('**/*.tile.openstreetmap.org/**',lambda r:r.abort())
    await c.route('**/router.project-osrm.org/**',lambda r:r.fulfill(status=503,body='offline walk fallback'))
    page=await c.new_page()
    await page.goto(args.url,wait_until='domcontentloaded')
    await page.wait_for_function("typeof map !== 'undefined' && map && davaoRoutes.every(r=>r.stopInfo)")
    return c,page

   c,page=await setup()
   await page.locator('#locate-btn').click()
   assert await page.evaluate('watches.length===1 && watches[0].options.enableHighAccuracy && watches[0].options.maximumAge===0')
   await page.evaluate('deliver(0,98782)')
   assert await page.evaluate('!userLocation && locationWatchId===0 && !awaitingMapPick')
   await page.evaluate('deliver(0,14)')
   assert await page.evaluate('userLocation.accuracy===14 && locationWatchId===null && locationGuard===null && cleared.includes(0)')
   await page.evaluate('deliver(0,98782,0,0)')
   assert await page.evaluate('userLocation.accuracy===14 && userLocation.lat!==0')
   await page.locator('#locate-btn').click()
   await page.evaluate('deliver(0,5,0,0);deliver(1,20)')
   assert await page.evaluate('userLocation.accuracy===20 && userLocation.lat!==0 && cleared.includes(1)')
   print(f'PASS {name}: coarse then precise, precise then stale coarse, watch ID 0 cleanup, repeated requests',flush=True)
   await c.close()

   c,page=await setup()
   await page.clock.install()
   await page.locator('#chat-input').fill('Abreeza')
   await page.locator('#search-btn').click()
   await page.evaluate('deliver(0,90000)')
   await page.clock.run_for(12001)
   assert await page.evaluate('awaitingMapPick && !userLocation && pendingDestination.key==="abreeza" && cleared.includes(0)')
   assert 'too broad' in await page.locator('#route-list').inner_text()
   await page.evaluate('map.setView(landmarks["matina-crossing"].coords,14,{animate:false})')
   point=await page.evaluate('({x:map.getSize().x/2,y:map.getSize().y/2})')
   await page.locator('#map').click(position=point)
   await page.wait_for_function('currentTrip && currentTrip.destination.key==="abreeza"')
   print(f'PASS {name}: broad-only timeout preserves destination; route-line map fallback plans trip',flush=True)
   await c.close()

   c,page=await setup()
   await page.clock.install()
   await page.locator('#locate-btn').click()
   await page.locator('#chat-input').fill('from Matina to Abreeza')
   await page.locator('#search-btn').click()
   await page.wait_for_function('!!currentTrip')
   await page.evaluate('deliver(0,14,0,0)')
   await page.clock.run_for(12001)
   assert await page.evaluate('userLocation.key==="matina-crossing" && !awaitingMapPick && cleared.includes(0) && locationGuard===null')
   print(f'PASS {name}: typed origin cancels watch and timer; stale callbacks cannot replace it',flush=True)
   await c.close()

   c,page=await setup()
   await page.locator('#chat-input').fill('Abreeza')
   await page.locator('#search-btn').click()
   await page.evaluate('watches[0].error({code:3});deliver(0,25)')
   await page.wait_for_function('currentTrip && currentTrip.destination.key==="abreeza"')
   assert await page.evaluate('userLocation.accuracy===25 && cleared.includes(0) && !awaitingMapPick')
   print(f'PASS {name}: transient timeout can recover; destination-only search uses accurate location',flush=True)
   await c.close()

   c,page=await setup()
   await page.locator('#locate-btn').click()
   await page.evaluate('watches[0].error({code:1})')
   assert await page.evaluate('awaitingMapPick && cleared.includes(0) && locationGuard===null')
   print(f'PASS {name}: permission denial stops watching and offers fallback',flush=True)
   await c.close()

   c,page=await setup('''() => Object.defineProperty(navigator,'geolocation',{value:undefined})''')
   await page.locator('#locate-btn').click()
   assert await page.evaluate('awaitingMapPick && locationGuard===null')
   await c.close()
   c,page=await setup('''() => Object.defineProperty(navigator,'geolocation',{value:{watchPosition(){throw new Error('unavailable')},clearWatch(){}}})''')
   await page.locator('#locate-btn').click()
   assert await page.evaluate('awaitingMapPick && locationGuard===null')
   print(f'PASS {name}: missing API and synchronous provider exception recover',flush=True)
   await c.close()
   await browser.close()

if __name__ == '__main__':
 parser = argparse.ArgumentParser(description='Mocked location-flow regressions in Firefox and installed Chrome.')
 parser.add_argument('--browsers', nargs='+', choices=['firefox', 'chromium'], default=['firefox', 'chromium'])
 parser.add_argument('--url', default='http://127.0.0.1:8000/')
 asyncio.run(main(parser.parse_args()))
