# Census and Crime Explorer

Explore the 2021 Census and Guelph Police calls for service (2021–2025) across Guelph's 201 neighbourhoods (Statistics Canada dissemination areas), and what crime nearby means for an area's wellbeing.

Built from [Guelph Census Explorer](../GuelphCensusExplorer) with a new **Crime and safety** measure group:

- **Seven crime measures** that map, rank, compare and relate like any census measure: a 0–100 crime pressure index, all incident calls nearby, and five groups (violence and threats; break-ins and vehicle theft; theft and vandalism; disturbances and disorder; collisions and driving complaints). Figures are police incident calls a year on the streets within a 5-minute walk (400 m) of each home, averaged over the homes in a neighbourhood.
- **Crime and wellbeing summary** at the top of every neighbourhood profile: a plain-language description, the most common call types, the 2021–2025 trend, and a note on how each high-ranking type affects wellbeing. Search an address and the summary switches to that exact address.
- **Relate crime to the census.** Pick a crime measure and any census measure in "How two measures relate" (it opens on crime pressure against population density).

- **Map any of 40 measures** across people, background, education and work, income, housing, commuting and access, with natural breaks (Jenks), quantile or equal-interval classes, 4 to 7 classes.
- **Neighbourhood profiles.** Tap a neighbourhood to see every measure beside the city figure, with a strip showing where it ranks among all 201.
- **Compare two neighbourhoods** side by side, with the difference for each measure.
- **See how two measures relate.** A scatter plot of any two measures with the correlation (r) explained in plain language. Tap a dot to open that neighbourhood.
- **Highest and lowest** five neighbourhoods for the mapped measure.
- **Find any address or street.** Search all 55,873 Guelph civic addresses: the app marks the address and opens its neighbourhood. Each neighbourhood is named after the two streets with the most length inside it.
- **City boundary** drawn from the City of Guelph's official boundary, with the area outside it faded.
- **Rotated to Guelph's grid.** The map is turned 46° clockwise so the city's street grid runs up and down and the city reads tall, with the Eramosa River heading to the upper right. A north arrow shows true north. The rotation is built into the map projection (`ROT_DEG` in `scripts/app.js`; negative turns clockwise), so clicks, search and zoom-to-fit all follow it.
- **Streets and buildings for context.** Main roads show at every zoom, collector and local streets fade in as you zoom, and street names follow the streets. All 38,908 building footprints appear from about zoom 14.5.

## Desktop and phone versions

- **`index.html` (desktop):** the map on the left, with a scrolling analysis panel on the right.
- **`mobile.html` (phone):** a full-screen map with search on top and a bottom tab bar (Measure, Profile, Relate, Rankings). The tabs open a sheet that slides up, and you can drag its handle between peek, half and full height. The peek strip always shows the mapped measure, the selected neighbourhood's value, and where it sits on the colour scale.

Phones and narrow windows (760 px or less) that open `index.html` are sent to `mobile.html` automatically. Each page links to the other, and a visitor who switches to desktop on a phone stays there.

A companion to [Guelph Census Explorer](../GuelphCensusExplorer) and [15-Minute Guelph](https://github.com/randyharris1999-cloud/15-Minute-Guelph). It includes that app's 15-minute score for each neighbourhood.

## What's in the folder

| Path | What it is |
|---|---|
| `index.html` | Desktop version |
| `mobile.html` | Phone version |
| `leaflet.min.js` | Leaflet 1.9.4 map library |
| `data/explorer.json` | Neighbourhood polygons, census values, city boundary, street names, water and main roads |
| `data/addresses.json` | Every civic address with its neighbourhood, loaded after the map so the page opens quickly |
| `data/context.json` | Building footprints and every named street segment, also loaded after the map |
| `scripts/build_explorer.py` | Builds both data files from the Census extract, `City_Boundary.geojson` and the 15-Minute Guelph `data/` folder |
| `scripts/app.js` | App code shared by both versions |
| `scripts/desktop.src.html`, `scripts/mobile.src.html` | Layout and styles for each version |
| `data/crime.json` | Police-call figures for every address, percentile tables, call types and yearly trends |
| `scripts/build_crime.py` | Builds `data/crime.json` and adds the crime measures to `data/explorer.json` |
| `scripts/build_html.py` | Combines each layout with `app.js` and the Leaflet stylesheet to write `index.html` and `mobile.html` |

## Publishing

Upload the folder to a new GitHub repository and turn on GitHub Pages (Settings → Pages → Deploy from branch → `main`, root). No Cloudflare relay is needed: the app has no live feeds.

To test locally, run `python -m http.server 8000` in the folder and open http://localhost:8000. Opening `index.html` directly from disk won't load the data.

## Rebuilding

1. Cut Guelph out of the Ontario Census Profile (`98-401-X2021006_English_CSV_data_Ontario.csv`, 8.8 GB) into `Guelph_DA_census_full.csv`: every characteristic for Guelph's 220 DAs and the City of Guelph census subdivision (DGUID `2021A00053523008`). Use the starting-row file to jump close to line 29,162,006, then keep rows whose DGUID is in `Guelph_DA_2021.geojson`.
2. Build the data and the page:

```
python scripts/build_explorer.py "<City of Guelph Data>/Census 2021" ../15-minute-guelph/data/ data/
python scripts/build_crime.py "<City of Guelph Data>" data/
python scripts/build_html.py
```

Run `build_crime.py` after `build_explorer.py`, because the census build rewrites `explorer.json` without the crime measures. It needs pandas, numpy, scipy and openpyxl, and reads every `.xlsx` in `<City of Guelph Data>/Crime Data/`, so dropping in a new year's file and re-running adds it (update `YEARS` at the top of the script).

To add a measure, add one line to the `M` list in `build_explorer.py` with its Census Profile characteristic IDs. The app picks it up automatically.

## Data

| Data | Source |
|---|---|
| Population, age, income, low income, housing, commuting | Statistics Canada, 2021 Census of Population, dissemination areas (Statistics Canada Open Licence) |
| Addresses, city boundary, buildings, streets, water, neighbourhood names | City of Guelph Open Data |
| 15-minute score | 15-Minute Guelph |
| Police calls for service, 2021–2025 | Guelph Police Service |

Notes:

- Incomes are for 2020, when pandemic benefits raised some low incomes.
- City figures are Statistics Canada's own figures for the City of Guelph census subdivision.
- Most measures beyond population, age, households and income come from the 25% long-form sample, so small neighbourhoods can vary a lot.
- Work and commuting figures describe May 2021, during the pandemic.
- The app maps the 201 DAs that contain Guelph address points. The 19 others are mostly rural edges outside the city's address data.
- Values Statistics Canada suppressed for privacy appear as "Not reported".

Crime notes:

- Calls for service are not convictions or confirmed crimes. Of about 400,000 calls, 51,909 place-based incident calls are kept. Left out: administrative records and 911 hang-ups, traffic stops and other police-initiated work, wellness and mental-health calls, domestic calls, missing persons, fraud and sex offences (not tied to a place, or unfair to map).
- The police data gives a street name but no house number. Each street's calls are spread along its segments, half by length and half by the number of addresses on each segment, so long arterials blur where along them a call happened. 99.9% of kept calls match a City street.
- About 57,600 calls (14%) are logged to Wyndham St S, the address of Guelph Police headquarters, mostly administrative records filtered out above. Vehicle-theft reports logged there are also dropped.
- The crime pressure index weights violence 3×, break-ins and vehicle theft 2× and the other groups 1×, then ranks against all 55,873 Guelph addresses (0 = fewest calls nearby, 100 = most). The "typical address" figure is the median address.
- Busy places draw more calls partly because more people pass through them; neighbourhoods with shopping plazas show high theft from shoplifting.
- Crime and census links in the Relate chart describe places, not people, and do not show that one causes the other.
- Wellbeing notes draw on research on crime, fear of crime and health, e.g. [Lorenc et al. 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3666893/) and [Statistics Canada on perceptions of personal safety](https://www150.statcan.gc.ca/n1/pub/85-002-x/2011001/article/11577-eng.htm).

An independent project built on open data. Not an official City of Guelph service. Created by Randy Harris.
