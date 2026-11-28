# Sun Ledger

[Open Sun Ledger](https://coolcode.ca/sunledger/) to compare the mean daily solar energy reaching a horizontal square metre in six Canadian grid areas across six provinces. Choose two cities on the chart or [open a monthly city profile](https://coolcode.ca/sunledger/cities/).

<!-- coolcode:guide -->
Compare winter sunlight around Langley, Calgary, Winnipeg, Toronto, Montréal and Halifax. In December the 2001–2020 daily mean was 1.00 kWh/m² in Winnipeg and 1.17 in Toronto. Each city profile includes all twelve monthly averages and compares its latest available reading with the same calendar month in the baseline.
<!-- /coolcode:guide -->

## Reading the chart

The bars show all-sky surface shortwave energy, including the effects of clouds. Toggle the clear-sky markers to see POWER’s corresponding cloud-free estimates. Each city is represented by the NASA grid area at the coordinates shown on its profile. Both city selectors, month and period can be shared using the comparison URL. A rooftop installation also depends on tilt, shading, snow and panel efficiency.

The default view averages each calendar month across 2001–2020, giving all 20 years equal weight. Select a year for its own monthly values. The first table compares a selected month across every available year. The annual table weights monthly means by the number of calendar days in that month, including leap days. Incomplete years have a dash in the annual table. Percent differences use the lower all-sky value as the reference and are calculated before the energy values are rounded for display.

## Source and refresh

The [NASA POWER Monthly and Annual API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) provides the Renewable Energy community fields `ALLSKY_SFC_SW_DWN` and `CLRSKY_SFC_SW_DWN` in kWh/m²/day. POWER supplies satellite-derived gridded estimates. The [source methodology](https://power.larc.nasa.gov/docs/faqs/data/) describes the spatial and temporal resolution. Data were obtained from the NASA Langley Research Center POWER Project funded through the NASA Earth Science Directorate Applied Science Program.

The public [snapshot](https://coolcode.ca/sunledger/data/solar.json) gives the retrieval date, start and end dates, coordinates, source URLs, NASA dataset codes, column order and all paired monthly values in source precision. Coverage begins in January 2001. A month appears only after its calendar month has ended and NASA has published both parameters for all six places. New months may arrive with a lag. The refresh checks coordinates, units, missing-data flags, baseline completeness and continuity with the last good edition before publication. NASA's special month 13 is an annual aggregate and is excluded. Monthly refresh runs on the 7th at 14:36 UTC and can be triggered manually.

The browser downloads one static file from CoolCode. Changing a city, month, year or benchmark runs locally. The page stores no visitor input. The per-location NASA source links make direct requests only when opened.

## Build and verify

The repository includes a working snapshot for offline builds. Refreshing it requires a connection to the public NASA endpoint and no key.

```sh
python3 scripts/refresh.py  # optional network refresh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -m http.server --directory dist 8000
```

CI installs the pinned browser-test dependency, builds at a project subpath, checks desktop and mobile interactions, and deploys tested main builds using GitHub Pages. Run `python3 tests/browser_smoke.py` after installing Playwright and Chromium to repeat the check locally.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
