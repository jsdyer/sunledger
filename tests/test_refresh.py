import json
import unittest
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from refresh import FIELDS, OUT, PLACES, extract


class SnapshotTests(unittest.TestCase):
    def test_snapshot_has_valid_paired_months(self):
        data = json.loads(OUT.read_text())
        self.assertEqual(data['count'], len(data['rows']))
        periods = [row[0] for row in data['rows']]
        self.assertEqual(periods, sorted(set(periods)))
        self.assertTrue({f'{y}-{m:02}' for y in range(2001,2021) for m in range(1,13)} <= set(periods))
        self.assertEqual(set(data['sources']), set(PLACES))
        expected = ['month', *(f'{slug}_{sky}' for slug, *_ in PLACES.values() for sky in ('all', 'clear'))]
        self.assertEqual(data['columns'], expected)
        self.assertTrue(all(len(row) == len(expected) and all(0 <= n <= 16 for n in row[1:]) for row in data['rows']))

    def test_annual_fill_and_unfinished_months_are_excluded(self):
        source = {'geometry': {'coordinates': [-63.58,44.65]}, 'header': {'fill_value': -999},
                  'parameters': {f: {'units':'kW-hr/m^2/day'} for f in FIELDS},
                  'properties': {'parameter': {f: {'202401':2, '202402':-999, '202403':4, '202413':3} for f in FIELDS}}}
        got = extract(source,44.65,-63.58,date(2024,3,31))
        self.assertEqual(got, {'2024-01':[2,2]})
        source['parameters'][FIELDS[0]]['units'] = 'W/m²'
        with self.assertRaisesRegex(ValueError,'units'):
            extract(source,44.65,-63.58,date(2024,3,31))
