#!/bin/bash
# Henter sykehus og helsesentre fra OpenStreetMap (Geofabrik-uttrekk) og lager data/helse.json
set -e
sudo apt-get install -y -qq osmium-tool >/dev/null
mkdir -p /tmp/osm data
fetch(){ curl -sfL --retry 3 -o "/tmp/osm/$1.pbf" "$2"; ls -l "/tmp/osm/$1.pbf"; }
fetch valencia https://download.geofabrik.de/europe/spain/valencia-latest.osm.pbf
fetch murcia https://download.geofabrik.de/europe/spain/murcia-latest.osm.pbf
fetch andalucia https://download.geofabrik.de/europe/spain/andalucia-latest.osm.pbf
fetch baleares https://download.geofabrik.de/europe/spain/islas-baleares-latest.osm.pbf
fetch canarias https://download.geofabrik.de/africa/canary-islands-latest.osm.pbf
for R in valencia murcia andalucia baleares canarias; do
  osmium tags-filter "/tmp/osm/$R.pbf" nwr/amenity=hospital,clinic,doctors nwr/healthcare=hospital,clinic,centre -o "/tmp/osm/$R-h.pbf" --overwrite
  osmium export "/tmp/osm/$R-h.pbf" -f geojsonseq -o "/tmp/osm/$R.geojsonseq" --overwrite
done
python3 - <<'PY'
import json, gzip
def pts(g):
    t, c = g["type"], g["coordinates"]
    if t == "Point": return [c]
    if t in ("LineString", "MultiPoint"): return c
    if t == "Polygon": return c[0]
    if t == "MultiPolygon": return [p for poly in c for p in poly[0]]
    return []
out = {}
for R in ["valencia", "murcia", "andalucia", "baleares", "canarias"]:
    els = []
    for line in open(f"/tmp/osm/{R}.geojsonseq"):
        line = line.strip().lstrip("\x1e")
        if not line: continue
        f = json.loads(line)
        p = pts(f["geometry"])
        if not p: continue
        els.append({"tags": f["properties"], "lat": sum(x[1] for x in p) / len(p), "lon": sum(x[0] for x in p) / len(p)})
    out[R] = els
print({k: len(v) for k, v in out.items()})
json.dump(out, gzip.open("data/osm-raw.json.gz", "wt"), ensure_ascii=False)
PY
python3 tools/build_helse.py
