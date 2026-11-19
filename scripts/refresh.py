"""Fetch paired NASA POWER monthly estimates and atomically replace the local edition."""
from calendar import monthrange
from datetime import date, datetime, timezone
import json
from math import isfinite
from pathlib import Path
import re
from time import sleep
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parents[1] / 'web/data/solar.json'
API = 'https://power.larc.nasa.gov/api/temporal/monthly/point'
FIELDS = ('ALLSKY_SFC_SW_DWN', 'CLRSKY_SFC_SW_DWN')
PLACES = {'Langley': (49.15, -122.66), 'Halifax': (44.65, -63.58)}
START = 2001


def fetch(url):
    request = Request(url, headers={'User-Agent': 'CoolCode Sun Ledger (github.com/jsdyer/sunledger)'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=90) as response:
                return json.load(response)
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            sleep(3 * (attempt + 1))


def extract(source, lat, lon, today):
    xy = source['geometry']['coordinates']
    if abs(xy[0] - lon) > .001 or abs(xy[1] - lat) > .001:
        raise ValueError('Unexpected source coordinates')
    if any(source['parameters'][field]['units'] != 'kW-hr/m^2/day' for field in FIELDS):
        raise ValueError('Unexpected source units')
    series = source['properties']['parameter']
    months = {}
    for key in series[FIELDS[0]]:
        if not re.fullmatch(r'\d{6}', key):
            raise ValueError(f'Unexpected POWER date {key}')
        year, month = int(key[:4]), int(key[-2:])
        if month == 13:  # POWER annual aggregate
            continue
        if not 1 <= month <= 12:
            raise ValueError(f'Invalid month {key}')
        period = date(year, month, 1)
        if period >= today.replace(day=1):
            continue
        pair = [series[field].get(key) for field in FIELDS]
        if any(value is None or value == source['header']['fill_value'] for value in pair):
            continue
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
               or not 0 <= value <= 16 for value in pair):
            raise ValueError(f'Invalid solar energy for {key}')
        months[period.strftime('%Y-%m')] = pair
    return months


def build_edition(today):
    sources, series = {}, []
    for place, (lat, lon) in PLACES.items():
        url = API + '?' + urlencode(dict(parameters=','.join(FIELDS), community='RE', longitude=lon,
                                          latitude=lat, start=START, end=today.year, format='JSON'))
        response = fetch(url)
        sources[place] = {'url': url, 'datasets': response['header']['sources'], 'latitude': lat, 'longitude': lon}
        series.append(extract(response, lat, lon, today))
    common = sorted(series[0].keys() & series[1].keys())
    baseline = {f'{year}-{month:02}' for year in range(2001, 2021) for month in range(1, 13)}
    if not baseline.issubset(common):
        raise ValueError('The complete 2001–2020 comparison period is required')
    if OUT.exists():
        old = json.loads(OUT.read_text())
        if not {row[0] for row in old['rows']}.issubset(common):
            raise ValueError('An upstream response omitted previously published periods')
    last_year, last_month = map(int, common[-1].split('-'))
    return {'retrieved': today.isoformat(), 'start': common[0] + '-01',
            'end': date(last_year, last_month, monthrange(last_year, last_month)[1]).isoformat(),
            'count': len(common), 'unit': 'kWh/m²/day', 'sources': sources,
            'columns': ['month', 'langley_all', 'langley_clear', 'halifax_all', 'halifax_clear'],
            'rows': [[month, *series[0][month], *series[1][month]] for month in common]}


if __name__ == '__main__':
    edition = build_edition(datetime.now(timezone.utc).date())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix('.tmp')
    temporary.write_text(json.dumps(edition, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
    temporary.replace(OUT)
    print(f"Updated {edition['count']} paired months through {edition['end']}")
