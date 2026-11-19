import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { annualDaily, baseline, format, seriesFor } from '../web/model.mjs';

const snapshot = JSON.parse(
  readFileSync(new URL('../web/data/solar.json', import.meta.url)),
);

test('ordinary December and June reproduce the two independently checked coast comparisons', () => {
  const series = seriesFor(snapshot.rows, baseline);
  assert.deepEqual([series[11][0], series[11][2]].map(format), [
    '0.68',
    '1.14',
  ]);
  assert.deepEqual([series[5][0], series[5][2]].map(format), ['5.52', '5.53']);
});

test('a single year is independent of the baseline and unavailable months stay missing', () => {
  const records = [
    ['2024-01', 1, 2, 3, 4],
    ['2025-02', 5, 6, 7, 8],
  ];
  const series = seriesFor(records, '2024');
  assert.deepEqual(series[0], [1, 2, 3, 4]);
  assert.equal(series[1], null);
  assert.equal(annualDaily(records, 2024), null);
  assert.equal(format(undefined), '—');
});

test('annual energy weights February by its actual length in leap years', () => {
  const rows = Array.from({ length: 12 }, (_, i) => [
    '2024-' + String(i + 1).padStart(2, '0'),
    ...Array(4).fill(i === 1 ? 10 : 0),
  ]);
  assert.deepEqual(annualDaily(rows, 2024), Array(4).fill(290 / 366));
});
