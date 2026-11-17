#!/bin/bash
# Henter sykehus og helsesentre fra OpenStreetMap (Geofabrik-uttrekk) og lager data/helse.json
set -e
sudo apt-get install -y -qq osmium-tool >/dev/null
mkdir -p /tmp/osm data data/offisiell
# Offisielle kataloger fra Ministerio de Sanidad (offentlige helsesentre, legevakter, alle sykehus med eierform)
UA="Mozilla/5.0 (elenahjelpen.com)"
for u in https://www.sanidad.gob.es/estadEstudios/estadisticas/docs/siap/2026_C_Catal_Centros_AP.xlsx \
         https://www.sanidad.gob.es/estadEstudios/estadisticas/docs/siap/2026_C_Catal_disp_urg.xlsx \
         https://www.sanidad.gob.es/estadEstudios/estadisticas/sisInfSanSNS/ofertaRecursos/hospitales/docs/CNH_2025.xlsx; do
  curl -sfL --retry 2 -m 180 -A "$UA" -o "data/offisiell/$(basename $u)" "$u" || echo "FEIL: $u"
done
ls -l data/offisiell
fetch(){ curl -sfL --retry 3 -o "/tmp/osm/$1.pbf" "$2"; ls -l "/tmp/osm/$1.pbf"; }
fetch spania https://download.geofabrik.de/europe/spain-latest.osm.pbf
fetch canarias https://download.geofabrik.de/africa/canary-islands-latest.osm.pbf
for R in spania canarias; do
  osmium tags-filter "/tmp/osm/$R.pbf" nwr/amenity=hospital,clinic,doctors,dentist nwr/healthcare=hospital,clinic,centre,dentist -o "/tmp/osm/$R-h.pbf" --overwrite
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
for R in ["spania", "canarias"]:
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
pip install -q --break-system-packages openpyxl || pip install -q openpyxl
python3 tools/official.py
python3 tools/build_helse.py -v | head -120
