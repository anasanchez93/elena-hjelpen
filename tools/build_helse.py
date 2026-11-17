"""Lager data/helse.json (kompakt) fra data/osm-raw.json.gz.
Felt: [navn, lat, lon, type h|c, sektor pub|priv, akutt 0|1, adresse, telefon, nettside]
"""
import gzip, json, re, sys

raw = json.load(gzip.open("data/osm-raw.json.gz", "rt"))

EXCLUDE = re.compile(r"dent|odontolog|veterin|fisio|physio|est[eé]tic|aesthetic|podolog|[oó]ptic|optic|psicolog|psycholog|"
                     r"laborator|farmacia|pharmac|logoped|audio|nutrici|dermoest|capilar|hair|botox|beauty|belleza|"
                     r"osteop|quiropr|chiropr|acupunt|massag|masaje|tattoo|vet\b|animal|mascota|rehabilit|reconocimiento|"
                     r"psiqui|fertilidad|reproducci|ivi\b|ginefiv|cirug[ií]a pl[aá]stica|centro de d[ií]a|residencia|geri[aá]tric|"
                     r"mutua|fremap|asepeyo|ibermutua|umivale|mc mutual|solimat|donaci[oó]n|transfusi|hemodi[aá]lisis|di[aá]lisis|"
                     r"prevenci[oó]n|drogodepend|adicci|ucad|uca\b|salud mental|usm\b|conductas adictivas|planificaci[oó]n familiar|"
                     r"centro de salud sexual|crema|sanatorio animal", re.I)
EXCL_HC = {"dentist", "physiotherapist", "optometrist", "psychotherapist", "podiatrist", "laboratory", "pharmacy",
           "alternative", "audiologist", "speech_therapist", "occupational_therapist", "nutrition_counselling",
           "rehabilitation", "blood_donation", "dialysis", "counselling", "sample_collection", "vaccination_centre"}

PUB_OP = re.compile(r"generalitat|conselleria|conseller[ií]a|servicio andaluz|\bsas\b|servicio murciano|\bsms\b|"
                    r"servicio canario|\bscs\b|consejer[ií]a|sanidad|ayuntamiento|ajuntament|diputaci[oó]n|"
                    r"departamento de salud|departament de salut|ag[eè]ncia valenciana|gobierno de canarias|junta de andaluc|"
                    r"ministerio|seguridad social|insalud|servicio de salud|sistema nacional|p[uú]blic|government|"
                    r"comunidad aut[oó]noma|regi[oó]n de murcia|cabildo", re.I)
PRIV_OP = re.compile(r"quir[oó]n|vithas|\bhla\b|imed|hospiten|sanitas|asisa|adeslas|dkv|viamed|xanit|helicópteros|"
                     r"medimar|perpetuo socorro|san jaime|clinica|cl[ií]nica|policl[ií]nica|centro m[eé]dico|medical|"
                     r"medic center|health ?care|international|privad|private|ochoa|ascires|nisa|hc marbella|"
                     r"cruz roja|red cross|sl\b|s\.l\.|s\.a\.|grupo", re.I)
PUB_NAME = re.compile(r"centro de salud|centre de salut|consultorio|consultori|\bpac\b|\bsuap\b|punto de atenci[oó]n continuada|"
                      r"punt d'atenci[oó]|centro de especialidades|centre d'especialitats|\bcaps?\b|centro de atenci[oó]n primaria|"
                      r"servicio (normal|especial) de urgencias|\bsnu\b|\bseu\b|dispositivo de cuidados cr[ií]ticos|\bdccu\b|"
                      r"centro de salud auxiliar|hospital general|hospital universitario|hospital comarcal|hospital de alta resoluci[oó]n|"
                      r"\bchare\b|\bhar\b|hospital marina baixa|hospital vega baja|hospital del mar menor|hospital rafael m[eé]ndez|"
                      r"hospital virgen|hospital reina sof|hospital regional|hospital costa del sol|hospital doctor|hospital dr\.? ", re.I)


def tags_text(t, *keys):
    return " ".join(t.get(k, "") for k in keys)


def classify(t):
    ot = t.get("operator:type", "").lower()
    name = t.get("name", "")
    op = tags_text(t, "operator", "operator:es", "brand", "network")
    if ot in ("public", "government", "governmental", "state", "municipal"):
        return "pub"
    if ot in ("private", "commercial", "business", "non_profit", "religious", "charity", "ngo"):
        return "priv"
    if PUB_OP.search(op) and not re.search(r"quir|vithas|hla|imed|hospiten", op, re.I):
        return "pub"
    if PRIV_OP.search(op):
        return "priv"
    if re.search(r"quir[oó]n|vithas|\bhla\b|\bimed\b|hospiten|xanit|medimar|perpetuo socorro|san jaime|viamed|"
                 r"cl[ií]nica|clinic|policl[ií]nica|centro m[eé]dico|medical|m[eé]dico\b|international|internacional|"
                 r"sanitas|asisa|dkv|\bhc\b|ochoa|helicopter", name, re.I):
        return "priv"
    if PUB_NAME.search(name):
        return "pub"
    return None


def kind(t):
    if t.get("amenity") == "hospital" or t.get("healthcare") == "hospital":
        return "h"
    return "c"


def addr(t):
    s = " ".join(x for x in [t.get("addr:street", ""), t.get("addr:housenumber", "")] if x).strip()
    town = t.get("addr:city") or t.get("addr:town") or t.get("addr:village") or t.get("addr:municipality") or ""
    parts = [p for p in [s, (t.get("addr:postcode", "") + " " + town).strip()] if p]
    return ", ".join(parts) or t.get("addr:full", "")


out, seen, unknown = [], set(), []
for prov, els in raw.items():
    for e in els:
        t = e.get("tags", {})
        name = (t.get("name") or t.get("name:es") or "").strip()
        if not name:
            continue
        if t.get("healthcare") in EXCL_HC or t.get("healthcare:speciality", "").split(";")[0] in ("dentistry", "physiotherapy", "veterinary", "ophthalmology", "psychiatry", "dermatology"):
            continue
        if EXCLUDE.search(name) or EXCLUDE.search(t.get("healthcare:speciality", "")):
            continue
        if t.get("disused:amenity") or t.get("abandoned:amenity"):
            continue
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        if lat is None:
            continue
        k = kind(t)
        s = classify(t)
        if s is None:
            unknown.append((prov, k, name, t.get("operator", "")))
            continue
        key = (name.lower(), round(lat, 3), round(lon, 3))
        if key in seen:
            continue
        seen.add(key)
        urg = 1 if t.get("emergency") == "yes" or re.search(r"urgencia|\bpac\b|\bsuap\b|atenci[oó]n continuada|\bsnu\b|\bseu\b|\bdccu\b", name, re.I) else 0
        phone = t.get("phone") or t.get("contact:phone") or ""
        web = t.get("website") or t.get("contact:website") or ""
        out.append([name, round(lat, 5), round(lon, 5), k, s, urg, addr(t), phone.split(";")[0].strip(), web.split(";")[0].strip()])

out.sort(key=lambda r: (r[3], r[0]))
json.dump(out, open("data/helse.json", "w"), ensure_ascii=False, separators=(",", ":"))
from collections import Counter
print(len(out), Counter((r[3], r[4]) for r in out))
print("ukjente:", len(unknown))
if "-v" in sys.argv:
    for u in unknown:
        print("  ?", u)
    for r in out:
        if r[3] == "h":
            print("  H", r[4], r[0], "|", r[6])
