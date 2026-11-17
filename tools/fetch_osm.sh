#!/bin/bash
# Henter sykehus og helsesentre fra OpenStreetMap (Overpass), én provins om gangen
mkdir -p /tmp/osm data
SERVERS="https://overpass-api.de/api/interpreter https://overpass.private.coffee/api/interpreter https://maps.mail.ru/osm/tools/overpass/api/interpreter https://overpass.kumi.systems/api/interpreter"
for P in A MU MA GC TF AL V GR; do
  Q="[out:json][timeout:240];
area[\"ISO3166-2\"=\"ES-$P\"]->.a;
(
 nwr[\"amenity\"=\"hospital\"](area.a);
 nwr[\"healthcare\"=\"hospital\"](area.a);
 nwr[\"amenity\"=\"clinic\"](area.a);
 nwr[\"healthcare\"~\"^(clinic|centre)$\"](area.a);
 nwr[\"amenity\"=\"doctors\"][\"name\"~\"entro|onsultori|l[ií]nica|[eé]dic|ospital|rgencia|PAC|SUAP\"](area.a);
);
out center tags;"
  ok=0
  for try in 1 2; do
    for u in $SERVERS; do
      code=$(curl -s -m 300 -o /tmp/osm/$P.json -w "%{http_code}" --data-urlencode "data=$Q" "$u")
      n=$(python3 -c "import json;print(len(json.load(open('/tmp/osm/$P.json'))['elements']))" 2>/dev/null || echo -1)
      echo "$P $u -> $code ($n)"
      if [ "$code" = "200" ] && [ "$n" -gt 0 ]; then ok=1; break 2; fi
      sleep 10
    done
  done
  [ $ok = 1 ] || rm -f /tmp/osm/$P.json
done
python3 - <<'PY'
import json,glob,gzip,os
out={}
for f in glob.glob('/tmp/osm/*.json'):
    out[os.path.basename(f)[:-5]]=json.load(open(f))['elements']
print({k:len(v) for k,v in out.items()})
json.dump(out,gzip.open('data/osm-raw.json.gz','wt'),ensure_ascii=False)
PY
