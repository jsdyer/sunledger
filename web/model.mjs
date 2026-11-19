export const months = Array.from({ length: 12 }, (_, i) =>
  new Intl.DateTimeFormat('en-CA', { month: 'long', timeZone: 'UTC' }).format(
    Date.UTC(2000, i, 1),
  ),
);
export const baseline = '2001–2020';
export const format = (value) => (value == null ? '—' : value.toFixed(2));
export const yearOf = (row) => Number(row[0].slice(0, 4));
export const monthOf = (row) => Number(row[0].slice(5));

export function selectedRows(rows, period) {
  return rows.filter((row) =>
    period === baseline
      ? yearOf(row) >= 2001 && yearOf(row) <= 2020
      : yearOf(row) === Number(period),
  );
}

export function seriesFor(rows, period) {
  const selected = selectedRows(rows, period);
  return months.map((_, index) => {
    const matches = selected.filter((row) => monthOf(row) === index + 1);
    if (!matches.length) return null;
    return [1, 2, 3, 4].map(
      (column) =>
        matches.reduce((sum, row) => sum + row[column], 0) / matches.length,
    );
  });
}

export function annualDaily(rows, year) {
  const annual = rows.filter((row) => yearOf(row) === Number(year));
  if (new Set(annual.map(monthOf)).size !== 12 || annual.length !== 12)
    return null;
  const days = annual.map((row) =>
    new Date(Date.UTC(year, monthOf(row), 0)).getUTCDate(),
  );
  const totalDays = days.reduce((a, b) => a + b, 0);
  return [1, 2, 3, 4].map(
    (column) =>
      annual.reduce((sum, row, index) => sum + row[column] * days[index], 0) /
      totalDays,
  );
}
