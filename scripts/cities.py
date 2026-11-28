"""Publish searchable city profiles from the same snapshot used by the comparison."""
from calendar import month_name
from html import escape
from statistics import mean
from xml.etree import ElementTree as ET

BASE = 'https://coolcode.ca/sunledger/'
METHODS = 'https://power.larc.nasa.gov/docs/services/api/temporal/monthly/'


def page(stage, path, title, description, content):
    dest = stage / path
    dest.mkdir(parents=True, exist_ok=True)
    up = '../' * len(path.strip('/').split('/'))
    (dest / 'index.html').write_text(f'''<!doctype html>
<html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Sun Ledger</title><meta name="description" content="{escape(description, quote=True)}">
<link rel="canonical" href="{BASE}{path}"><link rel="stylesheet" href="{up}style.css"></head>
<body><a class="skip" href="#main">Skip to readings</a>
<header><nav><a href="{up}">← Sun Ledger</a><a href="https://coolcode.ca/">CoolCode</a></nav></header>
<main id="main" class="profile"><h1>{escape(title)}</h1><p class="intro">{escape(description)}</p>{content}</main>
<footer><a href="{up}cities/">All city profiles</a><a href="https://coolcode.ca/about/#our-commitments">How CoolCode works</a></footer>
</body></html>''', encoding='utf-8')


def city_pages(stage, data):
    latest = data['rows'][-1]
    year, month = map(int, latest[0].split('-'))
    baseline = [row for row in data['rows'] if '2001' <= row[0][:4] <= '2020']
    by_month = [[row for row in baseline if int(row[0][5:]) == m] for m in range(1, 13)]
    if any(len(rows) != 20 for rows in by_month):
        raise ValueError('City profiles require 20 observations for every baseline month')

    entries, paths = [], ['cities/']
    for name, source in sorted(data['sources'].items()):
        slug = source['slug']
        path = f'cities/{slug}/'
        paths.append(path)
        column = data['columns'].index(slug + '_all')
        clear = data['columns'].index(slug + '_clear')
        normals = [mean(row[column] for row in group) for group in by_month]
        clear_normals = [mean(row[clear] for row in group) for group in by_month]
        entries.append(f'<li><a href="./{slug}/">{escape(name)}, {escape(source["province"])}</a>'
                       f' <span>December {normals[11]:.2f} · June {normals[5]:.2f} kWh/m²/day</span></li>')
        rows = ''.join(f'<tr><th scope="row">{month_name[m]}</th><td>{normals[m-1]:.2f}</td>'
                       f'<td>{clear_normals[m-1]:.2f}</td></tr>' for m in range(1, 13))
        counterpart = 'halifax' if slug == 'langley' else 'langley'
        open_chart = f'../../?first={slug}&amp;second={counterpart}'
        peak = max(range(12), key=normals.__getitem__)
        description = (f'In the {name} area, a horizontal square metre received an average of '
                       f'{normals[11]:.2f} kWh per day in December and {normals[5]:.2f} in June over 2001–2020.')
        page(stage, path, f'Monthly solar energy in {name}, {source["province"]}', description, f'''
<p><a href="{open_chart}&amp;month=12">Compare {escape(name)} with another city →</a></p>
<h2>When is solar energy highest?</h2>
<p>{month_name[peak+1]} had the highest monthly average at {normals[peak]:.2f} kWh/m²/day in the 20-year baseline.</p>
<div class="tablewrap"><table><caption>Mean daily solar energy on a horizontal surface, 2001–2020 (kWh/m²/day)</caption>
<thead><tr><th scope="col">Month</th><th scope="col">All sky</th><th scope="col">Clear-sky estimate</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>Latest available month</h2>
<p>In {month_name[month]} {year}, NASA estimated {latest[column]:.2f} kWh/m²/day for this area.
The 2001–2020 average for {month_name[month]} was {normals[month-1]:.2f} kWh/m²/day.
<a href="{open_chart}&amp;month={month}&amp;period={year}">See this month in the chart</a>.</p>
<h2>Where the readings come from</h2>
<p>NASA POWER estimates sunlight for a grid area around {source["latitude"]:.2f}° N, {abs(source["longitude"]):.2f}° W.
All-sky values include cloud effects. Clear-sky values estimate the energy under cloud-free conditions.
Panel angle, shade, snow and efficiency also affect electricity from a rooftop system.</p>
<p>Source retrieved {escape(data["retrieved"])}.
<a href="{escape(source["url"], quote=True)}">NASA data for {escape(name)}</a> · <a href="{METHODS}">NASA POWER monthly methodology</a></p>''')

    page(stage, 'cities/', 'Canadian solar energy by city',
         'Choose a city to see its monthly sunlight, its strongest season and the latest NASA reading.',
         '<p>Compare June and December below. Each figure is the 2001–2020 average daily energy per horizontal square metre.</p>'
         '<ul class="places">' + ''.join(entries) + '</ul><p><a href="../">Compare any two cities →</a></p>')
    xml = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in paths:
        ET.SubElement(ET.SubElement(xml, 'url'), 'loc').text = BASE + path
    ET.ElementTree(xml).write(stage / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
