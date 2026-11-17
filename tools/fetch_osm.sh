#!/bin/sh
# Henter sykehus og helsesentre fra OpenStreetMap (Overpass)
set -e
Q='[out:json][timeout:600];
area["ISO3166-2"~"^ES-(A|MU|MA|GC|TF|AL|V|GR)$"]->.a;
(
 nwr["amenity"="hospital"](area.a);
 nwr["healthcare"="hospital"](area.a);
 nwr["amenity"="clinic"](area.a);
 nwr["healthcare"~"^(clinic|centre)$"](area.a);
 nwr["amenity"="doctors"]["name"~"[Cc]entro|[Cc]onsultori|[Cc]l[ií]nica|[Mm][eé]dic|[Hh]ospital|[Uu]rgencia|PAC|SUAP"](area.a);
);
out center tags;'
for u in https://overpass-api.de/api/interpreter https://overpass.kumi.systems/api/interpreter https://maps.mail.ru/osm/tools/overpass/api/interpreter; do
  if curl -sf -m 900 --data-urlencode "data=$Q" "$u" -o /tmp/osm.json && [ $(stat -c%s /tmp/osm.json) -gt 10000 ]; then break; fi
done
gzip -9c /tmp/osm.json > data/osm-raw.json.gz
ls -l data/
