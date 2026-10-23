#!/usr/bin/env python3
"""Saved Firefox/Marionette diagnostic; see README.md for modes and limitations."""
import argparse
import json, os, socket, subprocess, sys, time, threading, signal, tempfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.umask(0o077)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode', nargs='?', choices=['network-local', 'network', 'default', 'geoclue'], default='network-local')
parser.add_argument('--headful', action='store_true', help='Open a visible Firefox test window')
options = parser.parse_args()
mode = options.mode
headless = not options.headful
profile=Path(tempfile.mkdtemp(prefix='davao-native-geo-'+mode+'-'))
profile.mkdir(exist_ok=True)
prefs={'remote.prefs.recommended':False, 'marionette.port':2833, 'permissions.default.geo':1, 'browser.shell.checkDefaultBrowser':False, 'browser.aboutwelcome.enabled':False, 'browser.startup.page':0}
if mode.startswith('network'): prefs.update({'geo.provider.use_geoclue':False, 'geo.provider.use_portal':False})
if mode=='geoclue': prefs.update({'geo.provider.use_geoclue':True, 'geo.provider.use_portal':False})
if mode.endswith('-local'):prefs['geo.provider.network.url']='http://127.0.0.1:8001/v1/geolocate'
(profile/'user.js').write_text('\n'.join('user_pref('+json.dumps(k)+', '+json.dumps(v)+');' for k,v in prefs.items()))
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers()
  self.wfile.write(b'''<!doctype html><title>Native location diagnosis</title><h1>Firefox native geolocation</h1><button id="locate">Get location</button><pre id="status">Ready</pre><script>
  window.heartbeat=0;setInterval(()=>heartbeat++,100);
  window.readings=[];window.result={status:'ready'};
  document.getElementById('locate').onclick=()=>{
   const started=performance.now();result={status:'pending'};
   navigator.geolocation.watchPosition(p=>{ result={status:'success',accuracy:p.coords.accuracy,elapsed:performance.now()-started,latitude:p.coords.latitude,longitude:p.coords.longitude}; readings.push({accuracy:result.accuracy,elapsed:result.elapsed,inDavao:result.latitude>=6.7&&result.latitude<=7.7&&result.longitude>=125.1&&result.longitude<=126.0}); document.getElementById('status').textContent=JSON.stringify({...result,latitude:'private',longitude:'private'}); },e=>{result={status:'error',code:e.code,message:e.message,elapsed:performance.now()-started};document.getElementById('status').textContent=JSON.stringify(result);},{enableHighAccuracy:false,timeout:10000,maximumAge:0});
   window.returnedFromGeolocation=true;
  };
  </script>''')
 def do_POST(self):
  payload=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or '{}')
  print('LOCAL PROVIDER: request received; wifi access point count =',len(payload.get('wifiAccessPoints',[])),flush=True)
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
  self.wfile.write(b'{"location":{"lat":7.0736,"lng":125.6110},"accuracy":1234}')
 def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',8001),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
log_path = profile / 'provider.log'
env=os.environ.copy();env['MOZ_LOG']='timestamp,sync,Geolocation:5,GeoclueLocation:5,PortalLocation:5,NetworkGeolocationProvider:5,nsWifiMonitor:5'
env['MOZ_LOG_FILE']=str(log_path)
output=log_path.with_suffix('.stderr').open('w')
args=[os.environ.get('FIREFOX_BINARY', '/usr/lib/firefox/firefox'),'--no-remote','--profile',str(profile),'--marionette','--remote-allow-system-access']
if headless:args.append('--headless')
proc=subprocess.Popen(args,env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
s=None;counter=0
try:
 for _ in range(100):
  if proc.poll() is not None: raise RuntimeError('Firefox exited '+str(proc.returncode))
  try:s=socket.create_connection(('127.0.0.1',2833),timeout=.5);break
  except OSError:time.sleep(.2)
 if s is None:raise RuntimeError('Marionette not ready')
 s.settimeout(12)
 def receive():
  prefix=b''
  while not prefix.endswith(b':'):
   part=s.recv(1)
   if not part:raise EOFError('Marionette closed')
   prefix+=part
  length=int(prefix[:-1]);data=b''
  while len(data)<length:
   part=s.recv(length-len(data))
   if not part:raise EOFError('Marionette closed')
   data+=part
  return json.loads(data)
 print('GREETING',receive(),flush=True)
 def command(name,args={}):
  global counter
  counter+=1;payload=json.dumps([0,counter,name,args]).encode();s.sendall(str(len(payload)).encode()+b':'+payload)
  reply=receive()
  if reply[2]:raise RuntimeError(reply[2])
  return reply[3]
 def js(script):return command('WebDriver:ExecuteScript',{'script':script,'args':[],'newSandbox':False,'sandbox':None})
 print('SESSION',command('WebDriver:NewSession',{'capabilities':{'alwaysMatch':{}}})['capabilities']['browserVersion'],flush=True)
 command('Marionette:SetContext',{'value':'chrome'})
 print('PREFS',js('''return Object.fromEntries(Services.prefs.getChildList('geo.').map(k=>{let t=Services.prefs.getPrefType(k),v=t===128?Services.prefs.getBoolPref(k):t===64?Services.prefs.getIntPref(k):Services.prefs.getStringPref(k);if(typeof v==='string'&&v.includes('://'))v=v.split('?')[0];return[k,v]}));'''),flush=True)
 command('Marionette:SetContext',{'value':'content'})
 command('WebDriver:Navigate',{'url':'http://127.0.0.1:8001/'})
 print('BEFORE',js('return {heartbeat, result, secure:isSecureContext, ua:navigator.userAgent};'),flush=True)
 print('TRIGGER',js("document.getElementById('locate').click();return {returned:window.returnedFromGeolocation,heartbeat};"),flush=True)
 for _ in range(14):
  time.sleep(1)
  state=js("return {heartbeat,readings,result:{...result,latitude:result.latitude===undefined?undefined:'private',longitude:result.longitude===undefined?undefined:'private'}};")
  print('STATE',state,flush=True)
  result=state.get('value',state)
  if result['result']['status']=='error':break
except Exception as e:
 print('FAILURE',type(e).__name__,str(e)[:600],flush=True)
 raise
finally:
 if s:s.close()
 if proc.poll() is None:
  os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=4)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 server.shutdown();output.close()
 print('LOGS',str(log_path),flush=True)
