"""Lager data/helse.json (kompakt) fra data/osm-raw.json.gz.
Felt: [navn, lat, lon, type h|c, sektor pub|priv, akutt 0|1, adresse, telefon, nettside]
"""
import gzip, json, re, sys

raw = json.load(gzip.open("data/osm-raw.json.gz", "rt"))

EXCLUDE = re.compile(r"veterin|fisio|physio|est[eé]tic|aesthetic|podolog|[oó]ptic|optic|psicolog|psycholog|"
                     r"laborator|farmacia|pharmac|logoped|audio|nutrici|dermoest|capilar|\bhair\b|botox|beauty|belleza|"
                     r"osteop|quiropr|chiropr|acupunt|massag|masaje|tattoo|\bvet\b|animal|mascota|rehabilit|reconocimiento|"
                     r"psiqui|fertilidad|reproducci|ivi\b|ginefiv|cirug[ií]a pl[aá]stica|centro de d[ií]a|residencia|geri[aá]tric|"
                     r"mutua|fremap|asepeyo|ibermutua|umivale|mc mutual|solimat|donaci[oó]n|transfusi|hemodi[aá]lisis|di[aá]lisis|"
                     r"prevenci[oó]n|drogodepend|adicci|ucad|uca\b|salud mental|usm\b|conductas adictivas|planificaci[oó]n familiar|"
                     r"centro de salud sexual|\bcrema\b|sanatorio animal|psiqu?[aá]tric|cruz roja|creu roja|red cross|dorsia|bernabeu|"
                     r"naval hospital|l[aá]ser|depila|rejuvene|anti.?aging|antienvejec|\bspa\b|\bu[ñn]as\b|nails|medicina est|cirug[ií]a est|"
                     r"pod[oó]log|podiatr|quiropod|mútua|^metge$|^(torre|edificio|edifici|pabell[oó]n|bloque|m[oó]dulo|planta) ", re.I)
EXCL_HC = {"physiotherapist", "optometrist", "psychotherapist", "podiatrist", "laboratory", "pharmacy",
           "alternative", "audiologist", "speech_therapist", "occupational_therapist", "nutrition_counselling",
           "rehabilitation", "blood_donation", "dialysis", "counselling", "sample_collection", "vaccination_centre"}

PUB_OP = re.compile(r"generalitat|conselleria|conseller[ií]a|servicio andaluz|\bsas\b|servicio murciano|\bsms\b|"
                    r"servicio canario|\bscs\b|osakidetza|sergas|servizo galego|sespa|servicio de salud del principado|sacyl|sescam|\bses\b|"
                    r"servicio aragon[eé]s|servicio navarro|osasunbidea|rioja salud|ib-salut|ib salut|institut catal[aà] de la salut|catsalut|\bics\b|sermas|"
                    r"servicio madrile|consorci|consejer[ií]a|sanidad|ayuntamiento|ajuntament|diputaci[oó]n|"
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


PRIV_BRAND = re.compile(r"quir[oó]n|vithas|\bhla\b|\bimed\b|hospiten|juaneda|viamed|\bnisa\b|xanit|medimar|perpetuo socorro|"
                        r"rotger|sanitas|asisa|\bimq\b|teknon|dexeus|corachan|\bhm\b|ruber|recoletas|povisa|nuestra se[ñn]ora del rosario|hospital de barcelona|"
                        r"\bhla\b|cl[ií]nica universidad de navarra|vithas|olympia|"
                        r"\bdkv\b|casa de la salud|instituto valenciano de oncolog|san roque|sermesa|"
                        r"san juan de dios|sant joan de d[eé]u|clinic balear|cl[ií]nic balear|policl[ií]nica|cl[ií]nica|clinic\b|"
                        r"centro m[eé]dico|medical|international|internacional|\bhc\b|ochoa|\bhcb\b|ascires|ribera cmv|ribera povisa|"
                        r"victoria eugenia|helicopter", re.I)
PUB_EXTRA = re.compile(r"ambulatori|centre sanitari|centro sanitario|unidad b[aá]sica de salud|\bubs\b|^urgencias?$|^urg[eè]ncies$|"
                       r"casa del mar|instituto social de la marina|centro de sa[uú]de|osasun|anbulatorio|centre d.atenci[oó] prim|equip d.atenci[oó]|\beap\b|\bcuap\b|\babs\b|"
                       r"punto de atenci[oó]n continuada|\bpac\b|centro de salud|centre de salut|consultori|^centro salud|^cs |^c\.a\.e\.|^care |centro de alta resoluci|consultas externas", re.I)


def classify(t):
    name0 = t.get("name", "")
    if is_dent(t):
        return "pub" if re.search(r"salud bucodental|salut bucodental|\busbd\b|unidad de odontolog[ií]a|centro de salud|centre de salut|consultorio", name0, re.I) else "priv"
    if re.search(r"san juan de dios del aljarafe", name0, re.I):
        return "pub"
    if PRIV_BRAND.search(name0):
        return "priv"
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
    if PUB_NAME.search(name) or PUB_EXTRA.search(name):
        return "pub"
    # Sykehus uten privat merkenavn er nesten alltid offentlige
    if (t.get("amenity") == "hospital" or t.get("healthcare") == "hospital") and re.match(r"(hospital|hospitalet|complejo hospitalario|complex hospitalari)\b", name, re.I):
        return "pub"
    return None


DENT = re.compile(r"dent|odontolog|bucodental|ortodonc|implant|sonris|smile|dental|endodonc|periodonc", re.I)


def is_dent(t):
    return t.get("amenity") == "dentist" or t.get("healthcare") == "dentist" or "dentistry" in t.get("healthcare:speciality", "") \
        or (DENT.search(t.get("name", "")) and t.get("amenity") != "hospital")


def kind(t):
    n = t.get("name", "")
    if is_dent(t):
        return "d"
    if re.search(r"centro de salud|centre de salut|consultori|centro m[eé]dico|centre m[eè]dic|center of medical|^asisa$|"
                 r"^cs |^centro salud|^c\.a\.e\.|centro de especialidades|centre d.especialitats|\bubs\b|unidad b[aá]sica|ambulatori|centro asistencial|^cl[ií]nica|policl[ií]nica|dua clinic", n, re.I) \
       and not re.search(r"hospital", n, re.I):
        return "c"
    if t.get("amenity") == "hospital" or t.get("healthcare") == "hospital":
        return "h"
    return "c"


def addr(t):
    s = " ".join(x for x in [t.get("addr:street", ""), t.get("addr:housenumber", "")] if x).strip()
    town = t.get("addr:city") or t.get("addr:town") or t.get("addr:village") or t.get("addr:municipality") or ""
    parts = [p for p in [s, (t.get("addr:postcode", "") + " " + town).strip()] if p]
    return ", ".join(parts) or t.get("addr:full", "")


import math, os, unicodedata


def nrm(x):
    x = unicodedata.normalize("NFD", str(x or "").lower())
    return "".join(c for c in x if unicodedata.category(c) != "Mn")


GENERIC = set("""centro centre salud salut saude sanitario sanitari medico medica medic consultorio consultori local auxiliar
de del la las el los y i d l a en al cs c s csi cl ambulatorio ambulatori hospital hospitalario clinica clinic unidad basica zona area
urgencias urgencia urgencies punto atencion atencio continuada primaria especialidades especialitats servicio servei pac suap cac
sar cuap snu centro integrado integral integrat universitario universitari general comarcal provincial regional nuestra senora
virgen san santa sant dr doctor policlinica policlinico osasun etxea anbulatorioa barrio""".split())


def toks(x, extra=()):
    w = re.findall(r"[a-z0-9ñç]+", nrm(x))
    return {t for t in w if len(t) > 2 and t not in GENERIC and t not in extra}


def km(a, b, c, d):
    x, y = math.radians(c - a), math.radians(d - b)
    h = math.sin(x / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(y / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


# ---------- 1) OSM-punkter ----------
PUBLIC_NAME = re.compile(r"centro de sa[lu]u?d|centre de salut|centro salud|consultori|\bpac\b|\bsuap\b|\bcac\b|atenci[oó]n continuada|"
                         r"ambulatori|osasun|anbulatorio|\bcap\b|centre d.atenci[oó] prim|\bubs\b|unidad b[aá]sica|centro de especialidades|"
                         r"centre d.especialitats|^urg[eè]ncias?$|^urgencies$|hospital (general|universitari|comarcal|provincial|regional)", re.I)
osm, seen = [], set()
for prov, els in raw.items():
    for e in els:
        t = e.get("tags", {})
        name = (t.get("name") or t.get("name:es") or "").strip()
        if not name or t.get("disused:amenity") or t.get("abandoned:amenity"):
            continue
        if t.get("healthcare") in EXCL_HC or t.get("healthcare:speciality", "").split(";")[0] in ("physiotherapy", "veterinary", "ophthalmology", "psychiatry", "dermatology", "podiatry", "cosmetic_surgery", "plastic_surgery"):
            continue
        if EXCLUDE.search(name) or EXCLUDE.search(t.get("healthcare:speciality", "")):
            continue
        lat, lon = e.get("lat"), e.get("lon")
        if lat is None:
            continue
        key = (name.lower(), round(lat, 3), round(lon, 3))
        if key in seen:
            continue
        seen.add(key)
        osm.append({"name": name, "lat": lat, "lon": lon, "k": kind(t), "guess": classify(t), "t": t,
                    "tok": toks(name), "pubname": bool(PUBLIC_NAME.search(name)), "used": False})

GRID = {}
for i, o in enumerate(osm):
    GRID.setdefault((round(o["lat"] * 20), round(o["lon"] * 20)), []).append(i)


def near(lat, lon, r_km):
    cy, cx = round(lat * 20), round(lon * 20)
    n = int(r_km / 5) + 1
    for dy in range(-n, n + 1):
        for dx in range(-n, n + 1):
            for i in GRID.get((cy + dy, cx + dx), ()):
                o = osm[i]
                d = km(lat, lon, o["lat"], o["lon"])
                if d <= r_km:
                    yield d, o


def best_match(rec, lat, lon, r_km, want_h, anchor=False):
    """Finn OSM-punktet som er samme sted som den offisielle oppføringen."""
    town = toks(rec.get("muni")) | toks(rec.get("loc")) | toks(rec.get("prov"))
    rt = toks(rec["raw"], town)
    best = None
    for d, o in near(lat, lon, r_km):
        if o["k"] == "d" or (want_h and o["k"] != "h" and not re.search(r"hospital", o["name"], re.I)):
            continue
        shared = rt & (o["tok"] - town)
        score = None
        if shared:
            score = d - 2 * len(shared)
        elif d < 0.15 and (o["pubname"] or (want_h and o["k"] == "h")) and not PRIV_BRAND.search(o["name"]):
            score = d + 1
        elif not rt and d < (r_km if anchor else 0.6) and (o["pubname"] or (want_h and o["k"] == "h")) and not PRIV_BRAND.search(o["name"]) and (toks(o["name"]) <= town or not toks(o["name"])):
            score = d + 0.5   # «Consultorio de Algar» i landsbyen Algar
        if score is not None and (best is None or score < best[0]):
            best = (score, o)
    return best[1] if best else None


# ---------- 2) Offisielle punkter (offentlige helsesentre, legevakter, sykehus) ----------
off = json.load(open("data/oficial.json")) if os.path.exists("data/oficial.json") else []
out, missing = [], []
placed = []
for rec in off:
    lat, lon = rec.get("lat"), rec.get("lon")
    if lat is not None and (rec.get("prec") in ("expendeduria", "punto_recarga_electrica", "ngbe")
                            or (rec.get("anchor") and km(lat, lon, *rec["anchor"]) > 40)):
        lat = lon = None   # geokoderen traff feil sted
    want_h = rec["src"] == "h"
    m = None
    if lat is not None:
        m = best_match(rec, lat, lon, 0.4 if rec.get("prec") == "portal" else 2.5, want_h)
    elif rec.get("anchor"):
        m = best_match(rec, rec["anchor"][0], rec["anchor"][1], 12, want_h, anchor=True)
        if m and not (toks(rec["raw"], toks(rec["muni"]) | toks(rec["loc"])) & m["tok"]) and not m["pubname"]:
            m = None
    if m:
        m["used"] = True
        if lat is None or rec.get("prec") != "portal":
            lat, lon = m["lat"], m["lon"]
    if lat is None:
        missing.append(rec)
        continue
    t = m["t"] if m else {}
    web = (t.get("website") or t.get("contact:website") or "").split(";")[0].strip()
    adr = ", ".join(x for x in [rec.get("addr"), (rec.get("cp", "") + " " + str(rec.get("loc") or "")).strip()] if x)
    name = rec["name"]
    if rec["src"] == "urg" and rec.get("ubic"):
        name = f"{rec['name']} – {rec['ubic']}"
    urg = rec["urg"] or (1 if t.get("emergency") == "yes" else 0)
    row = [name, round(lat, 5), round(lon, 5), rec["kind"], rec["sec"], urg, adr, rec.get("tel", ""), web, rec.get("hor", "")]
    placed.append((rec, row))

# Slå sammen legevakt med helsesenteret den ligger i
aps = [(r, row) for r, row in placed if r["src"] == "ap"]
for rec, row in placed:
    if rec["src"] != "urg":
        continue
    host = None
    for r2, row2 in aps:
        if abs(row2[1] - row[1]) < .01 and abs(row2[2] - row[2]) < .01 and km(row[1], row[2], row2[1], row2[2]) < 0.15:
            host = row2
            break
    if host:
        host[5] = 1
        host[9] = (rec["name"] + ": " + rec.get("hor", "")).strip(": ")
        if not host[7] and row[7]:
            host[7] = row[7]
        row[0] = None
for rec, row in placed:
    if row[0]:
        out.append(row)

# Fjern OSM-dubletter av offentlige steder (samme bygning)
offpts = [(r[1], r[2]) for r in out]
OGRID = {}
for la, lo in offpts:
    OGRID.setdefault((round(la * 100), round(lo * 100)), []).append((la, lo))


def near_official(o, r_km):
    cy, cx = round(o["lat"] * 100), round(o["lon"] * 100)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for la, lo in OGRID.get((cy + dy, cx + dx), ()):
                if km(o["lat"], o["lon"], la, lo) <= r_km:
                    return True
    return False


# ---------- 3) Private steder og tannleger fra OSM ----------
dropped = 0
for o in osm:
    if o["used"]:
        continue
    t, name = o["t"], o["name"]
    if o["k"] == "d":
        sec = "pub" if (near_official(o, 0.06) or re.search(r"salud bucodental|salut bucodental|\busbd\b", name, re.I)) else "priv"
        k = "d"
    else:
        if o["pubname"] or o["guess"] == "pub":
            if near_official(o, 0.3) or not o["pubname"]:
                dropped += 1      # finnes allerede i den offisielle katalogen
                continue
            # Offentlig etter navnet («Centro de Salud …», «Hospital Universitario …»), men ikke funnet i katalogen ved adressen
            phone = (t.get("phone") or t.get("contact:phone") or "").split(";")[0].strip()
            web = (t.get("website") or t.get("contact:website") or "").split(";")[0].strip()
            k = "h" if o["k"] == "h" and re.search(r"hospital|complejo|complexo|hospitalari", name, re.I) else "c"
            out.append([name, round(o["lat"], 5), round(o["lon"], 5), k, "pub", 1 if (k == "h" or t.get("emergency") == "yes") else 0, addr(t), phone, web, ""])
            continue
        if o["guess"] != "priv" and not PRIV_BRAND.search(name):
            continue              # vet ikke hva det er – tas ikke med
        if near_official(o, 0.05) and not PRIV_BRAND.search(name):
            continue
        sec, k = "priv", ("h" if o["k"] == "h" and re.search(r"hospital|hospiten", name, re.I) else "c")
    phone = (t.get("phone") or t.get("contact:phone") or "").split(";")[0].strip()
    web = (t.get("website") or t.get("contact:website") or "").split(";")[0].strip()
    urg = 1 if t.get("emergency") == "yes" and k != "d" else 0
    out.append([name, round(o["lat"], 5), round(o["lon"], 5), k, sec, urg, addr(t), phone, web, ""])

out.sort(key=lambda r: (r[3], r[0]))
json.dump(out, open("data/helse.json", "w"), ensure_ascii=False, separators=(",", ":"))
from collections import Counter
print(len(out), Counter((r[3], r[4]) for r in out))
print("offisielle uten posisjon:", len(missing), Counter(r["src"] for r in missing), "| OSM offentlige droppet:", dropped)
if "-v" in sys.argv:
    for r in sorted(missing, key=lambda r: r["src"] != "h")[:150]:
        print("  MISSING", r["src"], r["name"], "|", r.get("addr"), r.get("muni"))
