"""Compare direct, boarding-access and alighting-egress paths using public OSRM.

Coordinates are latitude, longitude. Requests send them to the routing provider.
The server's configured routing profile determines the mode; the URL's `foot`
name does not establish that the route or returned duration is for pedestrians.
"""

import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def coordinate(value):
    try:
        latitude, longitude = (float(part.strip()) for part in value.split(','))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('use latitude,longitude') from exc
    if not (math.isfinite(latitude) and math.isfinite(longitude)
            and -90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise argparse.ArgumentTypeError('latitude must be -90..90 and longitude -180..180')
    return latitude, longitude


def router_url(value):
    parts = urllib.parse.urlsplit(value)
    if (parts.scheme not in ('http', 'https') or not parts.hostname
            or parts.query or parts.fragment or parts.username or parts.password):
        raise argparse.ArgumentTypeError('use an http(s) router base URL without credentials, query, or fragment')
    return value.rstrip('/')


def profile_name(value):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', value):
        raise argparse.ArgumentTypeError('use a profile name such as foot, driving, or bike')
    return value


def compare_path(label, start, end, *, router, profile, timeout, user_agent, steps=True):
    coordinates = f'{start[1]},{start[0]};{end[1]},{end[0]}'
    query = urllib.parse.urlencode({'overview': 'false', 'steps': str(steps).lower()})
    url = f'{router}/route/v1/{profile}/{coordinates}?{query}'
    request = urllib.request.Request(url, headers={'User-Agent': user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    if data.get('code') != 'Ok' or not data.get('routes'):
        raise ValueError(f'router returned {data.get("code", "no route")}')
    route = data['routes'][0]
    roads = list(dict.fromkeys(
        step['name'] for leg in route.get('legs', []) for step in leg.get('steps', [])
        if step.get('name')
    ))
    return {
        'case': label,
        'distance_m': route['distance'],
        'router_duration_s': route['duration'],
        'roads': roads,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True, type=coordinate, metavar='LAT,LNG')
    parser.add_argument('--destination', required=True, type=coordinate, metavar='LAT,LNG')
    parser.add_argument('--board', type=coordinate, metavar='LAT,LNG', help='estimated boarding point')
    parser.add_argument('--alight', type=coordinate, metavar='LAT,LNG', help='estimated alighting point')
    parser.add_argument('--router-url', type=router_url, default='https://router.project-osrm.org',
                        help='OSRM server base URL, optionally with a path prefix (default: %(default)s)')
    parser.add_argument('--profile', type=profile_name, default='foot',
                        help='profile name in the request URL; server must support the mode (default: %(default)s)')
    parser.add_argument('--timeout', type=float, default=12, metavar='SECONDS',
                        help='per-request timeout (default: %(default)s)')
    parser.add_argument('--interval', type=float, default=1, metavar='SECONDS',
                        help='minimum interval between request starts; honor provider policy (default: %(default)s)')
    parser.add_argument('--user-agent', default='DavaoRoutes-spike/1.0',
                        help='caller identity sent to the routing provider (default: %(default)s)')
    parser.add_argument('--steps', action=argparse.BooleanOptionalAction, default=True,
                        help='request turn steps and road names (default: enabled)')
    parser.add_argument('--format', choices=['jsonl', 'json'], default='jsonl',
                        help='one JSON object per path, or one JSON array (default: %(default)s)')
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be a positive finite number')
    if not math.isfinite(args.interval) or args.interval < 0:
        parser.error('--interval must be a nonnegative finite number')
    if not args.user_agent.strip() or '\n' in args.user_agent or '\r' in args.user_agent:
        parser.error('--user-agent must be a nonempty single line')

    paths = [('direct', args.origin, args.destination)]
    if args.board:
        paths.append(('access', args.origin, args.board))
    if args.alight:
        paths.append(('egress', args.alight, args.destination))

    failed = False
    results = []
    last_request = None
    for label, start, end in paths:
        if last_request is not None:
            time.sleep(max(0, args.interval - (time.monotonic() - last_request)))
        last_request = time.monotonic()
        try:
            result = compare_path(label, start, end, router=args.router_url, profile=args.profile,
                                  timeout=args.timeout, user_agent=args.user_agent, steps=args.steps)
        except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            failed = True
            result = {'case': label, 'error': f'{type(exc).__name__}: {exc}'}
        results.append(result)
        if args.format == 'jsonl':
            print(json.dumps(result), flush=True)
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
