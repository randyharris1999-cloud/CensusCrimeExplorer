"""Build data/crime.json and add crime measures to data/explorer.json.

usage: python scripts/build_crime.py "<City of Guelph Data>" data/

Reads:
  <City of Guelph Data>/Crime Data/*.xlsx      Guelph Police calls for service, one file per year
  <City of Guelph Data>/StreetCentrelines.geojson
  <City of Guelph Data>/Addresses.geojson      (address counts per street segment)
  data/addresses.json, data/explorer.json      (this app's addresses and neighbourhoods)

Method
  1. Keep calls whose dispatch type is a place-based incident, in five groups (CAT below).
     Admin records, 911 hang-ups, police-initiated stops, wellness/mental-health, domestic,
     missing persons, fraud and sex offences are left out (not tied to a place, or unfair to map).
  2. The police data gives a street name but no house number, so each street's calls are spread
     along its segments: half by segment length, half by the number of addresses on the segment.
  3. For every address, add up the calls a year on street lengths within 400 m (a 5-minute walk).
  4. A neighbourhood's figure is the average over its addresses.
Vehicle-theft calls logged to Wyndham St S are dropped: that is Guelph Police HQ (15 Wyndham St S),
where many such reports are taken.
"""
import sys, os, glob, json, math
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

SRC, OUT = sys.argv[1], sys.argv[2]
R = 400.0
YEARS = [2021, 2022, 2023, 2024, 2025]
CAT = {
    "violence": ["ASSAULT", "ROBBERY", "OFFENSIVE WEAPON", "THREATENING", "CRIMINAL HARASSMENT/STALKING", "HOMICIDE", "ABDUCTION"],
    "breakin":  ["BREAK & ENTER", "THEFT MOTOR VEHICLE", "PROWLER"],
    "theft":    ["THEFT UNDER $5000", "THEFT OVER $5000", "PROPERTY DAMAGE", "GRAFFITI"],
    "disorder": ["DISTURBANCE", "UNWANTED PERSON", "INTOXICATED PERSON", "DRUGS", "LIQUOR OFFENCE", "INDECENT ACT",
                 "PROSTITUTION", "YOUTH (UNDER 18) COMPLAINT", "NOISE COMPLAINT"],
    "road":     ["MVC PROP. DAMAGE", "MVC PERSONAL INJURY", "MVC HIT AND RUN", "DRIVING COMPLAINT", "IMPAIRED DRIVER", "MVC FATALITY"],
}
CATS = list(CAT)
WEIGHT = {"violence": 3, "breakin": 2, "theft": 1, "disorder": 1, "road": 1}
NICE = {  # plain names for dispatch types, used in the written summaries
    "ASSAULT": "assaults", "ROBBERY": "robberies", "OFFENSIVE WEAPON": "weapons calls", "THREATENING": "threats",
    "CRIMINAL HARASSMENT/STALKING": "harassment", "HOMICIDE": "homicide", "ABDUCTION": "abduction",
    "BREAK & ENTER": "break-ins", "THEFT MOTOR VEHICLE": "vehicle thefts", "PROWLER": "prowlers",
    "THEFT UNDER $5000": "thefts under $5,000", "THEFT OVER $5000": "thefts over $5,000", "PROPERTY DAMAGE": "property damage", "GRAFFITI": "graffiti",
    "DISTURBANCE": "disturbances", "UNWANTED PERSON": "unwanted-person calls", "INTOXICATED PERSON": "intoxicated people",
    "DRUGS": "drug calls", "LIQUOR OFFENCE": "liquor offences", "INDECENT ACT": "indecent acts", "PROSTITUTION": "sex-trade calls",
    "YOUTH (UNDER 18) COMPLAINT": "youth complaints", "NOISE COMPLAINT": "noise complaints",
    "MVC PROP. DAMAGE": "collisions with damage", "MVC PERSONAL INJURY": "injury collisions", "MVC HIT AND RUN": "hit-and-runs",
    "DRIVING COMPLAINT": "driving complaints", "IMPAIRED DRIVER": "impaired drivers", "MVC FATALITY": "fatal collisions",
}
T2C = {t: c for c, ts in CAT.items() for t in ts}
TYPES = list(T2C)

# ---- 1. calls
frames = []
for f in sorted(glob.glob(os.path.join(SRC, "Crime Data", "*.xlsx"))):
    d = pd.read_excel(f, usecols=["City", "Address", "ReportedDate", "DispatchType"], engine="openpyxl")
    frames.append(d); print(os.path.basename(f), len(d))
df = pd.concat(frames, ignore_index=True)
total_rows = len(df)
df = df[df.City.astype(str).str.strip() == "GUELPH"].copy()
df["typ"] = df.DispatchType.astype(str).str.replace(r"^\d-", "", regex=True).str.rstrip('"').str.strip()
df["st"] = df.Address.astype(str).str.strip()
df["yr"] = pd.to_datetime(df.ReportedDate).dt.year
df = df[df.typ.isin(TYPES) & df.yr.isin(YEARS)]
df = df[~((df.st == "WYNDHAM ST S") & (df.typ == "THEFT MOTOR VEHICLE"))]
print("incident calls kept", len(df))
ny = len(YEARS)
by_type = df.groupby(["st", "typ"]).size().unstack(fill_value=0).reindex(columns=TYPES, fill_value=0) / ny
by_year = df.groupby(["st", "yr"]).size().unstack(fill_value=0).reindex(columns=YEARS, fill_value=0)
city_year = {c: [int(((df.typ.map(T2C) == c) & (df.yr == y)).sum()) for y in YEARS] for c in CATS}
city_types = {c: sorted([[NICE[t], int((df.typ == t).sum())] for t in CAT[c]], key=lambda x: -x[1])[:4] for c in CATS}

# ---- 2. streets, densified every ~10 m, with per-type calls a year
LAT0 = 43.55; KX = 111320 * math.cos(math.radians(LAT0)); KY = 110574
proj = lambda lon, lat: ((np.asarray(lon) + 80.25) * KX, (np.asarray(lat) - LAT0) * KY)
A = json.load(open(os.path.join(SRC, "Addresses.geojson"), encoding="utf-8"))["features"]
aseg = pd.Series([a["properties"]["SEGMENTID"] for a in A]).value_counts()
G = json.load(open(os.path.join(SRC, "StreetCentrelines.geojson"), encoding="utf-8"))["features"]
segs = []
for f in G:
    if f["geometry"]["type"] != "LineString": continue
    p = f["properties"]; c = np.array(f["geometry"]["coordinates"])[:, :2]
    x, y = proj(c[:, 0], c[:, 1]); L = float(np.hypot(np.diff(x), np.diff(y)).sum())
    if L > 0: segs.append((p["STREETNAME"], x, y, L, int(aseg.get(p["SEGMENTID"], 0))))
sd = pd.DataFrame([(s[0], s[3], s[4]) for s in segs], columns=["st", "L", "na"]).groupby("st").sum()
matched = by_type.index.isin(sd.index)
print("calls on a matched street: %.2f%%" % (100 * by_type[matched].values.sum() / by_type.values.sum()))
P, VT, VY = [], [], []
for st, x, y, L, na in segs:
    if st not in by_type.index: continue
    tl, tn = sd.loc[st, "L"], sd.loc[st, "na"]
    share = 0.5 * L / tl + (0.5 * na / tn if tn > 0 else 0.5 * L / tl)
    d = np.concatenate([[0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))]); n = max(1, int(L // 10))
    s = (np.arange(n) + 0.5) * L / n
    P.append(np.c_[np.interp(s, d, x), np.interp(s, d, y)])
    VT.append(np.repeat((by_type.loc[st].values * share / n)[None, :], n, 0))
    VY.append(np.repeat((by_year.loc[st].values * share / n)[None, :], n, 0))
P, VT, VY = np.vstack(P), np.vstack(VT), np.vstack(VY)
tree = cKDTree(P)

# ---- 3. every address in this app
AD = json.load(open(os.path.join(OUT, "addresses.json"), encoding="utf-8"))
lon = np.cumsum(AD["x"]) / 1e5; lat = np.cumsum(AD["y"]) / 1e5; dai = np.array(AD["d"])
ax, ay = proj(lon, lat)
idx = tree.query_ball_point(np.c_[ax, ay], R)
ET = np.array([VT[i].sum(0) if i else np.zeros(len(TYPES)) for i in idx])   # calls a year by type
EY = np.array([VY[i].sum(0) if i else np.zeros(ny) for i in idx])           # calls by year (all groups)
cidx = {c: [TYPES.index(t) for t in CAT[c]] for c in CATS}
EC = np.c_[[ET[:, cidx[c]].sum(1) for c in CATS]].T                         # calls a year by group
W = np.array([WEIGHT[c] for c in CATS]); EW = EC @ W

def pct_table(v):  # 101 percentile cut points, address-weighted, for client-side ranking
    return [round(float(x), 2) for x in np.percentile(v, np.arange(101))]

# ---- 4. neighbourhoods
E = json.load(open(os.path.join(OUT, "explorer.json"), encoding="utf-8"))
E["measures"] = [m for m in E["measures"] if m.get("group") != "Crime and safety"]
for a in E["das"]:
    for k in list(a):
        if k.startswith("cr_"): del a[k]
nda = len(E["das"]); da_types, da_year = [None] * nda, [None] * nda
for i, a in enumerate(E["das"]):
    m = dai == i
    if not m.any(): continue
    ec = EC[m].mean(0); a["cr_all"] = round(float(ec.sum()), 1)
    for j, c in enumerate(CATS): a["cr_" + c] = round(float(ec[j]), 1)
    et = ET[m].mean(0); da_types[i] = [[NICE[TYPES[j]], round(float(et[j]), 1)] for j in np.argsort(-et)[:6] if et[j] >= 0.5]
    da_year[i] = [round(float(v), 1) for v in EY[m].mean(0)]
# safety index: weighted calls, as a percentile among all Guelph addresses (0 = fewest, 100 = most)
cut = np.array(pct_table(EW))
for i, a in enumerate(E["das"]):
    m = dai == i
    if m.any(): a["cr_idx"] = int(np.clip(np.searchsorted(cut, EW[m].mean()) - 1, 0, 100))
med = lambda v: round(float(np.median(v)), 1)
E["city"]["cr_all"] = med(EC.sum(1))
for j, c in enumerate(CATS): E["city"]["cr_" + c] = med(EC[:, j])
E["city"]["cr_idx"] = 50
NEW = [
    ("cr_idx", "Crime pressure index", "Incident calls to police on the streets within a 5-minute walk of each home, weighted by seriousness (violence 3×, break-ins 2×, others 1×) and ranked against every Guelph address: 0 is the fewest, 100 the most. 2021–2025 average.", "idx"),
    ("cr_all", "All incident calls nearby", "Police incident calls a year on the streets within a 5-minute walk (400 m), averaged over the homes in the area. 2021–2025."),
    ("cr_violence", "Violence and threats", "Assaults, robberies, weapons calls, threats and harassment a year within a 5-minute walk. 2021–2025 average."),
    ("cr_breakin", "Break-ins and vehicle theft", "Break-and-enters, vehicle thefts and prowler calls a year within a 5-minute walk. 2021–2025 average."),
    ("cr_theft", "Theft and vandalism", "Thefts (mostly shoplifting), property damage and graffiti calls a year within a 5-minute walk. 2021–2025 average."),
    ("cr_disorder", "Disturbances and disorder", "Disturbance, unwanted-person, intoxicated-person, drug and similar calls a year within a 5-minute walk. 2021–2025 average."),
    ("cr_road", "Collisions and driving complaints", "Collisions, hit-and-runs, impaired and dangerous driving calls a year within a 5-minute walk. 2021–2025 average."),
]
for row in NEW:
    k, label, desc = row[:3]
    E["measures"].append({"key": k, "group": "Crime and safety", "label": label, "desc": desc, "kind": row[3] if len(row) > 3 else "calls", "ramp": "red", "city": "typical address"})
json.dump(E, open(os.path.join(OUT, "explorer.json"), "w", encoding="utf-8"), separators=(",", ":"))

# ---- 5. crime.json: per-address group figures (x10, ints), percentile tables, citywide context
crime = {
    "years": YEARS, "cats": CATS, "weight": [WEIGHT[c] for c in CATS], "radius": R,
    "a": [[int(round(v * 10)) for v in EC[:, j]] for j in range(len(CATS))],
    "pct": {c: pct_table(EC[:, j]) for j, c in enumerate(CATS)},
    "pct_all": pct_table(EC.sum(1)), "pct_w": pct_table(EW),
    "da_types": da_types, "da_year": da_year,
    "city_year": city_year, "city_types": city_types,
    "kept": int(len(df)), "rows": int(total_rows),
}
json.dump(crime, open(os.path.join(OUT, "crime.json"), "w", encoding="utf-8"), separators=(",", ":"))
print("wrote crime.json and updated explorer.json;", nda, "neighbourhoods,", len(ax), "addresses")
