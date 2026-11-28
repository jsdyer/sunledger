import {
  annualDaily,
  baseline,
  format,
  monthOf,
  months,
  seriesFor,
  yearOf,
} from './model.mjs';

const byId = (id) => document.getElementById(id);
const colours = ['#a64820', '#246b65'];
let edition;
let years;
let comparisonRows;
let cities;

function selectCities() {
  cities = [byId('first').value, byId('second').value];
  const columns = cities.map(name => edition.columns.indexOf(edition.sources[name].slug + '_all'));
  comparisonRows = edition.rows.map(row => [row[0], ...columns.flatMap(i => row.slice(i, i + 2))]);
  cities.forEach((name, index) => {
    const side = index === 0 ? 'first' : 'second';
    const site = edition.sources[name];
    byId(side + '-legend').textContent = name;
    const profile = byId(side + '-profile');
    profile.textContent = name;
    profile.href = './cities/' + site.slug + '/';
    const source = byId(index === 0 ? 'west-source' : 'east-source');
    source.href = site.url;
    source.textContent = name + ' NASA data ↗';
  });
}

function rememberSelection() {
  const url = new URL(location.href);
  url.searchParams.set('first', edition.sources[cities[0]].slug);
  url.searchParams.set('second', edition.sources[cities[1]].slug);
  url.searchParams.set('month', byId('month').value);
  url.searchParams.set('period', byId('period').value);
  history.replaceState(null, '', url);
}


function svgElement(tag, attributes, parent, text) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attributes))
    node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  parent.append(node);
  return node;
}

function drawChart(series, selected, showClear) {
  const host = byId('chart');
  host.replaceChildren();
  const width = Math.max(295, Math.round(host.clientWidth));
  const left = 27,
    right = 5,
    top = 12;
  const height = width < 440 ? 216 : 270;
  const bottom = height - 31;
  const step = (width - left - right) / 12;
  const bar = Math.min(20, step * 0.3);
  const peak = Math.max(...series.filter(Boolean).flat());
  const ceiling = Math.max(10, Math.ceil(peak / 2) * 2);
  const y = (value) => bottom - (value / ceiling) * (bottom - top);
  const chart = svgElement(
    'svg',
    {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label':
        'Monthly all-sky energy at both cities. Exact values are available using the month menu.',
    },
    host,
  );
  svgElement(
    'rect',
    {
      x: left + selected * step + 1,
      y: top - 3,
      width: step - 2,
      height: height - top - 1,
      fill: '#eee6d5',
    },
    chart,
  );
  for (let tick = 0; tick <= ceiling; tick += 2) {
    svgElement(
      'line',
      {
        x1: left,
        y1: y(tick),
        x2: width - right,
        y2: y(tick),
        stroke: '#c8c2b3',
        'stroke-width': 0.8,
      },
      chart,
    );
    svgElement(
      'text',
      { x: left - 6, y: y(tick) + 4, 'text-anchor': 'end', 'font-size': 12 },
      chart,
      String(tick),
    );
  }
  series.forEach((row, index) => {
    const mid = left + (index + 0.5) * step;
    if (row) {
      colours.forEach((colour, city) => {
        const x = mid + (city ? 1 : -bar - 1);
        const value = row[city * 2];
        svgElement(
          'rect',
          {
            x,
            y: y(value),
            width: bar,
            height: bottom - y(value),
            fill: colour,
          },
          chart,
        );
        if (showClear) {
          const ref = y(row[city * 2 + 1]);
          svgElement(
            'line',
            {
              x1: x,
              x2: x + bar,
              y1: ref,
              y2: ref,
              stroke: colour,
              'stroke-width': 3,
            },
            chart,
          );
        }
      });
    }
    svgElement(
      'text',
      {
        x: mid,
        y: height - 8,
        'text-anchor': 'middle',
        'font-size': width < 445 ? 11 : 13,
        'font-weight': index === selected ? 750 : 450,
      },
      chart,
      months[index].slice(0, width < 420 ? 1 : 3),
    );
    const hit = svgElement(
      'rect',
      {
        x: left + index * step,
        y: top,
        width: step,
        height: height - top,
        fill: 'transparent',
        cursor: 'pointer',
      },
      chart,
    );
    svgElement(
      'title',
      {},
      hit,
      row
        ? `${months[index]} · ${cities[0]} ${format(row[0])}, ${cities[1]} ${format(row[2])} kWh/m²/day`
        : `${months[index]} · Not available`,
    );
    hit.addEventListener('click', () => {
      byId('month').value = index + 1;
      render();
      rememberSelection();
    });
  });
}

function tableHeading(id, clear) {
  const tr = document.createElement('tr');
  const labels = cities.flatMap(name => clear
    ? [name + ' all-sky', name + ' clear-sky']
    : [name + ' all-sky']);
  for (const label of ['Year', ...labels]) {
    const cell = document.createElement('th');
    cell.scope = 'col';
    cell.textContent = label;
    tr.append(cell);
  }
  byId(id).replaceChildren(tr);
}

function tableBody(id, data, period, clear) {
  const fragment = document.createDocumentFragment();
  for (const [year, values] of data) {
    const row = document.createElement('tr');
    const head = document.createElement('th');
    head.scope = 'row';
    head.textContent = year;
    row.append(head);
    if (String(year) === period) row.classList.add('current');
    for (const index of clear ? [0, 1, 2, 3] : [0, 2]) {
      const cell = document.createElement('td');
      cell.textContent = format(values?.[index]);
      row.append(cell);
    }
    fragment.append(row);
  }
  byId(id).replaceChildren(fragment);
}

function render() {
  const period = byId('period').value;
  const index = Number(byId('month').value) - 1;
  const clear = byId('benchmark').checked;
  const series = seriesFor(comparisonRows, period);
  const values = series[index];
  const label = period === baseline ? baseline + ' average' : period;
  byId('period-note').textContent =
    period === baseline
      ? 'Average for each month, 2001–2020.'
      : `Monthly averages for ${period} · ${series.filter(Boolean).length} of 12 months available.`;
  byId('read-period').textContent = label;
  byId('chosen').textContent = months[index];
  byId('marker-key').hidden = !clear;
  drawChart(series, index, clear);
  for (const [city, offset] of [
    ['first-energy', 0],
    ['second-energy', 2],
  ]) {
    byId(city).textContent = format(values?.[offset]);
    const ref = byId(city + '-ref');
    ref.hidden = !clear;
    ref.textContent = 'Clear sky ' + format(values?.[offset + 1]);
  }
  if (values && Math.min(values[0], values[2]) > 0) {
    const ratio =
      Math.max(values[0], values[2]) / Math.min(values[0], values[2]);
    const difference = Math.round((ratio - 1) * 100);
    const brighter = values[0] > values[2] ? cities[0] : cities[1];
    byId('difference').textContent = difference
      ? `${brighter} receives about ${difference}% more all-sky energy per day this month.`
      : 'All-sky daily energy differs by less than 1% between the two cities.';
  } else {
    byId('difference').textContent = values
      ? 'A percentage comparison needs two positive values.'
      : 'Paired estimates are unavailable for this month.';
  }
  byId('month-summary').textContent = `${months[index]} values by year`;
  byId('table-caption').textContent =
    `${months[index]} daily mean energy at both locations (kWh/m²/day). Dashes mark missing months.`;
  tableHeading('thead', clear);
  tableHeading('annual-head', clear);
  tableBody(
    'history',
    years.map((year) => [
      year,
      comparisonRows
        .find((r) => yearOf(r) === year && monthOf(r) === index + 1)
        ?.slice(1),
    ]),
    period,
    clear,
  );
  tableBody(
    'annual',
    years.map((year) => [year, annualDaily(comparisonRows, year)]),
    period,
    clear,
  );
}

async function start() {
  const response = await fetch('./data/solar.json');
  if (!response.ok) throw new Error('Snapshot unavailable');
  edition = await response.json();
  years = [...new Set(edition.rows.map(yearOf))].reverse();
  byId('period').add(new Option(baseline + ' average', baseline));
  for (const year of years) byId('period').add(new Option(String(year), year));
  months.forEach((name, i) => byId('month').add(new Option(name, i + 1)));
  const query = new URLSearchParams(location.search);
  const names = Object.keys(edition.sources);
  for (const [index, side] of ['first', 'second'].entries()) {
    const select = byId(side);
    for (const name of [...names].sort((a,b) => a.localeCompare(b)))
      select.add(new Option(name + ', ' + edition.sources[name].province, name));
    select.value = names.find(name => edition.sources[name].slug === query.get(side))
      || (index === 0 ? 'Langley' : 'Halifax');
    select.addEventListener('change', () => {
      const other = byId(index === 0 ? 'second' : 'first');
      if (other.value === select.value) other.value = cities[index];
      selectCities();
      render();
      rememberSelection();
    });
  }
  if (byId('first').value === byId('second').value)
    byId('second').value = names.find(name => name !== byId('first').value);
  selectCities();
  byId('period').value = years.includes(Number(query.get('period'))) ? query.get('period') : baseline;
  const requestedMonth = Number(query.get('month'));
  byId('month').value = requestedMonth >= 1 && requestedMonth <= 12 && Number.isInteger(requestedMonth)
    ? requestedMonth : 12;
  const chooseAvailableMonth = () => {
    const series = seriesFor(comparisonRows, byId('period').value);
    if (!series[Number(byId('month').value) - 1])
      byId('month').value = series.findLastIndex(Boolean) + 1;
  };
  chooseAvailableMonth();
  byId('period').addEventListener('change', () => {
    chooseAvailableMonth();
    render();
    rememberSelection();
  });
  byId('month').addEventListener('change', () => { render(); rememberSelection(); });
  byId('benchmark').addEventListener('change', render);
  byId('coverage').textContent =
    `${edition.count} paired months from ${edition.start.slice(0, 7)} through ${edition.end.slice(0, 7)}. Retrieved ${edition.retrieved}. The archive updates monthly. Annual means appear after both locations have all 12 months.`;
  byId('load').hidden = true;
  byId('work').hidden = false;
  render();
  let previousWidth = byId('chart').clientWidth;
  new ResizeObserver(() => {
    const current = byId('chart').clientWidth;
    if (current !== previousWidth) {
      previousWidth = current;
      render();
    }
  }).observe(byId('chart'));
}

start().catch(() => {
  byId('load').hidden = false;
  byId('load').textContent =
    'The solar record could not be loaded. Reload the page to try again.';
});
