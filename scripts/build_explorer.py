"""Build data/explorer.json for Guelph Census Explorer.

Inputs
  CENSUS  folder holding Guelph_DA_census_full.csv (every 2021 Census Profile characteristic for
          Guelph's DAs and the City of Guelph CSD, cut from 98-401-X2021006_English_CSV_data_Ontario.csv)
          and Guelph_DA_2021.geojson
  FMG     the 15-Minute Guelph data folder (census.json for the 15-minute score and DA outlines,
          water.json and streetnames.json for the basemap)
Usage
  python build_explorer.py "<Census 2021 folder>" "<15-minute-guelph/data>" data/
"""
import csv, json, math, collections, os, sys

CENSUS, FMG, OUT = (sys.argv[1:4] + [None] * 3)[:3]
CENSUS = CENSUS or "/mnt/user-data/uploads/Documents/City of Guelph Data/Census 2021/"
FMG = FMG or "../randyharris1999-cloud/15-minute-guelph/data/"
OUT = OUT or "data/"
CITY = "2021A00053523008"

# ---------- read the profile ----------
V = collections.defaultdict(dict)        # DGUID -> {char_id: value}
for r in csv.DictReader(open(os.path.join(CENSUS, "Guelph_DA_census_full.csv"), encoding="utf-8")):
    v = r["C1_COUNT_TOTAL"].strip()
    try: V[r["DGUID"]][int(r["CHARACTERISTIC_ID"])] = float(v)
    except ValueError: pass                 # blank, x, F, .. = suppressed / not available

def val(g, i): return V[g].get(i)
def share(g, num, den):
    n = sum(val(g, i) or 0 for i in num) if isinstance(num, (list, tuple)) else val(g, num)
    d = val(g, den)
    if n is None or not d: return None
    return round(100 * n / d, 1)

# ---------- measures ----------
# kind: n (count), d (number with one decimal), pct, money, score
# get(g) returns the value for a DA or for the city. city_note explains the city figure.
P = lambda num, den: (lambda g: share(g, num, den))
I = lambda i: (lambda g: val(g, i))
M = [
  # People
  ("pop",      "People", "Residents", "People counted in 2021.", "n", "teal", I(1)),
  ("density",  "People", "People per km²", "Residents per square kilometre of land.", "n", "teal", I(6)),
  ("age",      "People", "Median age", "Half the residents are older than this.", "d", "amber", I(40)),
  ("kids",     "People", "Children 0–14", "Share of residents aged 14 and under.", "pct", "green", P(9, 8)),
  ("youth",    "People", "Young adults 20–34", "Share of residents aged 20 to 34.", "pct", "teal", P([15, 16, 17], 8)),
  ("seniors",  "People", "Seniors 65 and over", "Share of residents aged 65 and over.", "pct", "amber", P(24, 8)),
  ("hhsize",   "People", "Average household size", "People per household.", "d", "green", I(57)),
  ("alone",    "People", "People living alone", "Share of households with one person.", "pct", "amber", P(51, 50)),
  ("families", "People", "Couples with children", "Share of households that are a couple with children.", "pct", "green", P(103, 100)),
  ("loneparent","People", "One-parent families", "Share of households that are one-parent families.", "pct", "amber", P(105, 100)),
  ("movers",   "People", "Moved in the last 5 years", "Share of residents who lived at another address in 2016.", "pct", "teal", P(1985, 1983)),
  # Background
  ("immig",    "Background", "Immigrants", "Share of residents born outside Canada who have settled here.", "pct", "teal", P(1529, 1527)),
  ("recent",   "Background", "Recent immigrants", "Share of residents who immigrated between 2016 and 2021.", "pct", "teal", P(1536, 1527)),
  ("vismin",   "Background", "Visible minority", "Share of residents who belong to a visible minority, as defined by the Employment Equity Act.", "pct", "teal", P(1684, 1683)),
  ("tongue",   "Background", "Mother tongue not English or French", "Share of residents whose first language learned is neither official language.", "pct", "teal", P(398, 393)),
  # Education and work
  ("degree",   "Education and work", "University degree", "Share of 25 to 64 year olds with a bachelor's degree or higher.", "pct", "teal", P(2024, 2014)),
  ("nocert",   "Education and work", "No diploma", "Share of 25 to 64 year olds with no certificate, diploma or degree.", "pct", "amber", P(2015, 2014)),
  ("unemp",    "Education and work", "Unemployment rate", "Share of the labour force out of work in May 2021.", "pct", "amber", I(2230)),
  ("partic",   "Education and work", "Labour force participation", "Share of people 15 and over working or looking for work.", "pct", "teal", I(2228)),
  ("wfh",      "Education and work", "Worked from home", "Share of employed people who worked at home in May 2021, during the pandemic.", "pct", "teal", P(2594, 2593)),
  ("outside",  "Education and work", "Work outside Guelph", "Share of commuters with a usual workplace outside the city.", "pct", "amber", P([2600, 2601, 2602], 2598)),
  # Income
  ("income",   "Income", "Median household income", "Total household income in 2020, before tax.", "money", "teal", I(243)),
  ("aftertax", "Income", "Median after-tax household income", "Household income in 2020, after tax.", "money", "teal", I(244)),
  ("indinc",   "Income", "Median individual income", "Total income in 2020 of people 15 and over who had income.", "money", "teal", I(113)),
  ("lowinc",   "Income", "Low income (LIM-AT)", "Share of residents below the low-income measure, after tax.", "pct", "amber", I(345)),
  # Housing
  ("renters",  "Housing", "Households that rent", "Share of households renting their home.", "pct", "amber", P(1416, 1414)),
  ("detached", "Housing", "Single-detached houses", "Share of homes that are single-detached houses.", "pct", "green", P(42, 41)),
  ("towers",   "Housing", "Apartments 5+ storeys", "Share of homes in apartment buildings of five or more storeys.", "pct", "teal", P(47, 41)),
  ("condo",    "Housing", "Condominiums", "Share of homes that are condominiums.", "pct", "teal", P(1419, 1418)),
  ("old",      "Housing", "Homes built before 1961", "Share of homes built in 1960 or earlier.", "pct", "amber", P(1441, 1440)),
  ("new",      "Housing", "Homes built since 2001", "Share of homes built from 2001 to 2021.", "pct", "green", P([1445, 1446, 1447, 1448], 1440)),
  ("value",    "Housing", "Median home value", "Owners' estimate of what their home would sell for, 2021.", "money", "teal", I(1488)),
  ("rent",     "Housing", "Median monthly rent", "Median monthly shelter cost for renters, 2021.", "money", "amber", I(1494)),
  ("burden",   "Housing", "Paying 30%+ on housing", "Share of households spending 30% or more of income on shelter.", "pct", "amber", P(1467, 1465)),
  ("coreneed", "Housing", "Core housing need", "Share of households in core housing need: housing that costs too much, is too small or needs major repairs, with no affordable local alternative.", "pct", "amber", P(1480, 1479)),
  ("crowded",  "Housing", "Crowded homes", "Share of households in homes without enough bedrooms (not suitable).", "pct", "amber", P(1439, 1437)),
  # Getting to work
  ("car",      "Getting to work", "Commute by car", "Share of commuters who drive or ride in a car, truck or van.", "pct", "amber", P(2604, 2603)),
  ("transit",  "Getting to work", "Commute by transit", "Share of commuters who take the bus or train.", "pct", "teal", P(2607, 2603)),
  ("active",   "Getting to work", "Commute on foot or by bike", "Share of commuters who walk or cycle.", "pct", "green", P([2608, 2609], 2603)),
]

# ---------- geometry and the 15-minute score from 15-Minute Guelph ----------
FM = {d["da"]: d for d in json.load(open(os.path.join(FMG, "census.json")))}
W = json.load(open(os.path.join(FMG, "water.json")))
SN = json.load(open(os.path.join(FMG, "streetnames.json")))
KX, KY = 111320 * math.cos(math.radians(43.55)), 110540

def dec(fl):
    x = y = 0; pts = []
    for j in range(0, len(fl), 2):
        x += fl[j]; y += fl[j + 1]; pts.append((x / 1e5, y / 1e5))
    return pts
def enc(pts):
    fl = []
    for x, y in pts: fl += [round(x * 1e5), round(y * 1e5)]
    return fl
def pip(x, y, ring):
    ins = False; n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: ins = not ins
    return ins
def area_km2(ring):
    s = 0
    for i in range(len(ring)):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % len(ring)]
        s += (x1 * KX) * (y2 * KY) - (x2 * KX) * (y1 * KY)
    return abs(s) / 2 / 1e6

das = []
for da, d in FM.items():
    rings = [[(fl[j] / 1e5, fl[j + 1] / 1e5) for j in range(0, len(fl), 2)] for fl in d["rings"]]
    bb = [(min(p[0] for p in r), max(p[0] for p in r), min(p[1] for p in r), max(p[1] for p in r)) for r in rings]
    das.append({"da": da, "g": "2021S0512" + da, "rings": rings, "bb": bb, "score": d["score"], "n": d["n"]})

# name each DA after the streets with the most length inside it
length = [collections.Counter() for _ in das]
for ni, cls, fl in SN["segs"]:
    pts = dec(fl); name = SN["names"][ni]
    for a, b in zip(pts, pts[1:]):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        L = math.hypot((b[0] - a[0]) * KX, (b[1] - a[1]) * KY)
        for k, D in enumerate(das):
            if any(x0 <= mx <= x1 and y0 <= my <= y1 and pip(mx, my, r) for r, (x0, x1, y0, y1) in zip(D["rings"], D["bb"])):
                length[k][name] += L; break

out = []
for k, D in enumerate(das):
    g = D["g"]
    if g not in V: print("no census rows for", D["da"]); continue
    rec = {"da": D["da"], "streets": [n for n, _ in length[k].most_common(6)],
           "rings": [enc(r) for r in D["rings"]],
           "area": round(sum(area_km2(r) for r in D["rings"]), 4),
           "hh": val(g, 50), "pop": val(g, 1)}
    for key, *_rest, fn in M: rec[key] = fn(g)
    rec["score"] = D["score"]
    out.append(rec)

# city figures straight from the City of Guelph census subdivision row
city = {key: fn(CITY) for key, *_r, fn in M}
popw = sum(r["pop"] or 0 for r in out)
city["score"] = round(sum((r["pop"] or 0) * r["score"] for r in out) / popw, 1)

measures = [{"key": k, "group": grp, "label": lab, "desc": desc, "kind": kind, "ramp": ramp} for k, grp, lab, desc, kind, ramp, fn in M]
measures.append({"key": "score", "group": "Access", "label": "15-minute score", "desc": "Average 15-Minute Guelph score (0–100) of the addresses inside. The city figure is the average resident's score.", "kind": "score", "ramp": "score"})

water = [[name, [enc(dec(r)) for r in rings]] for name, area, rings in W]
streets = [[cls, enc(dec(fl))] for ni, cls, fl in SN["segs"] if cls >= 2]
hwy = [enc(dec(fl)) for ramp, fl in SN.get("hwy", []) if not ramp]
json.dump({"measures": measures, "city": city, "das": out, "water": water, "streets": streets, "hwy": hwy},
          open(os.path.join(OUT, "explorer.json"), "w"), separators=(",", ":"))

print(len(out), "neighbourhoods,", len(measures), "measures,", os.path.getsize(os.path.join(OUT, "explorer.json")) // 1024, "KB")
for m in measures:
    vals = [r[m["key"]] for r in out if r[m["key"]] is not None]
    print(f'{m["key"]:10} n={len(vals):3} min={min(vals):>9} max={max(vals):>9} city={city[m["key"]]}')

# ---------- addresses and city boundary (searchable addresses, boundary outline) ----------
A = json.load(open(os.path.join(FMG, "addresses.json")))
grid = collections.defaultdict(list)          # 0.01-degree buckets of DA indexes for fast lookup
OI = []
for k, rec in enumerate(out):
    D = next(x for x in das if x["da"] == rec["da"]); OI.append(D)
    for (x0, x1, y0, y1) in D["bb"]:
        for gx in range(int(x0 * 100) - 1, int(x1 * 100) + 1):
            for gy in range(int(y0 * 100) - 1, int(y1 * 100) + 1): grid[(gx, gy)].append(k)
def da_of(x, y):
    for k in grid.get((int(x * 100) - (x < 0), int(y * 100)), []):   # int() truncates toward zero for negatives
        if any(pip(x, y, r) for r in OI[k]["rings"]): return k
    for k in set(grid.get((int(x * 100) - 1, int(y * 100)), []) + grid.get((int(x * 100), int(y * 100)), [])):
        if any(pip(x, y, r) for r in OI[k]["rings"]): return k
    return -1
T, X, Y, DI = [], [], [], []
px = py = 0; miss = 0
order = sorted(range(len(A["text"])), key=lambda i: A["text"][i])
for i in order:
    x, y = A["lon"][i], A["lat"][i]
    k = da_of(x / 1e5, y / 1e5)
    if k < 0: miss += 1; continue
    T.append(A["text"][i]); X.append(x - px); Y.append(y - py); DI.append(k); px, py = x, y
json.dump({"t": T, "x": X, "y": Y, "d": DI}, open(os.path.join(OUT, "addresses.json"), "w"), separators=(",", ":"))
print(len(T), "addresses placed,", miss, "outside the mapped neighbourhoods,", os.path.getsize(os.path.join(OUT, "addresses.json")) // 1024, "KB")

B = json.load(open(os.path.join(CENSUS, "..", "City_Boundary.geojson")))["features"][0]["geometry"]
polys = [B["coordinates"]] if B["type"] == "Polygon" else B["coordinates"]
bound = [enc([(round(x, 5), round(y, 5)) for x, y in ring]) for p in polys for ring in p]
J = json.load(open(os.path.join(OUT, "explorer.json"))); J["boundary"] = bound
json.dump(J, open(os.path.join(OUT, "explorer.json"), "w"), separators=(",", ":"))
print("boundary rings", len(bound), "points", sum(len(b) // 2 for b in bound))

# ---------- context layer: building footprints, all streets with names (loaded after the map) ----------
BLD = json.load(open(os.path.join(FMG, "buildings.json")))          # delta-encoded E5 rings
segs_all = [[ni, cls, fl] for ni, cls, fl in SN["segs"]]              # delta-encoded E5 lines
json.dump({"b": BLD, "names": SN["names"], "s": segs_all}, open(os.path.join(OUT, "context.json"), "w"), separators=(",", ":"))
print("context:", len(BLD), "buildings,", len(segs_all), "street segments,", os.path.getsize(os.path.join(OUT, "context.json")) // 1024, "KB")
