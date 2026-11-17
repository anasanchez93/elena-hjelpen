"""Leser de offisielle katalogene fra Ministerio de Sanidad og geokoder adressene med CartoCiudad (IGN).
Resultat: data/oficial.json. Geokoding lagres i data/geocache.json, så bare nye adresser slås opp neste gang.

  python3 tools/official.py            # med geokoding (kjøres i GitHub Actions)
  python3 tools/official.py --offline  # bare cache
"""
import json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
import openpyxl

D = "data/offisiell/"
OFFLINE = "--offline" in sys.argv
CACHE_F = "data/geocache.json"
cache = json.load(open(CACHE_F)) if os.path.exists(CACHE_F) else {}


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


SMALL = {"de", "del", "la", "las", "el", "los", "y", "i", "d", "l", "a", "en", "s/n", "sn"}


def pretty(s):
    """«TORREVIEJA - PATRICIO PÉREZ» -> «Torrevieja - Patricio Pérez»"""
    out = []
    for i, w in enumerate(str(s or "").split()):
        lw = w.lower()
        if re.fullmatch(r"([a-z]\.)+[a-z]?\.?|[ivx]+|c\.s\.i\.?|s/n|sn", lw):
            out.append(w.upper() if lw not in ("s/n", "sn") else "s/n")
        elif i and lw in SMALL:
            out.append(lw)
        else:
            out.append("-".join(p[:1].upper() + p[1:] for p in lw.split("-")))
    t = " ".join(out).replace("Nº", "nº")
    t = re.sub(r"(-\s+|\(\s*)([a-zà-ÿ])", lambda m: m.group(1) + m.group(2).upper(), t)   # stor bokstav etter «-» og «(»
    t = re.sub(r"\(([A-Za-z]{2,5})\)", lambda m: "(" + m.group(1).upper() + ")", t)          # (PAC), (SUAP)
    return t


def rows(f, sheet):
    ws = openpyxl.load_workbook(D + f, read_only=True)[sheet]
    it = ws.iter_rows(values_only=True)
    head = next(it)
    return [dict(zip(head, r)) for r in it if any(r)]


def clean_addr(a):
    a = str(a or "")
    a = re.sub(r"\s*-\s*$", "", a)
    a = re.sub(r",?\s*S/N", "", a, flags=re.I)
    a = re.sub(r"\bN[ºO°]\s*", "", a)
    return a.strip(" ,")


def geocode(q):
    if q in cache:
        return cache[q]
    if OFFLINE:
        return None
    url = "https://www.cartociudad.es/geocoder/api/geocoder/findJsonp?q=" + urllib.parse.quote(q)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "elenahjelpen.com kart"}), timeout=30) as r:
                txt = r.read().decode("utf-8", "replace")
            m = re.search(r"\((.*)\)\s*;?\s*$", txt, re.S)
            j = json.loads(m.group(1) if m else txt)
            res = None
            if j:
                la, lo = float(j.get("lat") or 0), float(j.get("lng") or 0)
                if not (la and lo) and j.get("geom"):
                    pts = re.findall(r"(-?\d+\.\d+) (-?\d+\.\d+)", j["geom"])
                    if pts and not str(j["geom"]).startswith("MULTIPOLYGON") and not str(j["geom"]).startswith("POLYGON"):
                        lo, la = map(float, pts[len(pts) // 2])
                if la and lo:
                    res = [round(la, 6), round(lo, 6), str(j.get("type") or ""), norm(j.get("muni") or ""), j.get("portalNumber")]
            cache[q] = res
            return res
        except Exception as e:
            time.sleep(2 + attempt * 3)
    return None


def locate(addr, cp, loc, muni, prov):
    """Prøv adresse+postnummer+sted, så adresse+kommune, og sjekk at treffet ligger i riktig kommune."""
    a = clean_addr(addr)
    a = re.sub(r",\s*(\d+[A-Z]?)\b", r" \1", a)          # «Calle X, 6» -> «Calle X 6»
    a = re.sub(r"\s*-\s*(urb|urbanizaci[oó]n|bajo|local|edificio|esquina|pda|partida)\b.*$", "", a, flags=re.I)
    tries = []
    if a:
        towns = []
        for x in [loc] + re.split(r"/", str(muni or "")):
            x = re.sub(r"\s*\((.*)\)$", lambda m: "", str(x or "")).strip()
            if x and x.lower() not in [t.lower() for t in towns]:
                towns.append(x)
        tries += [f"{a}, {t}" for t in towns]
    for q in tries:
        g = geocode(q)
        if g and g[2] not in ("Municipio", "municipio", "poblacion", "Poblacion", "provincia", "comunidad autonoma"):
            gm, mm = g[3], norm(muni)
            if not gm or gm[:5] in mm or mm[:5] in gm or any(p[:5] in gm for p in re.split(r"[/ ]", mm) if len(p) > 3):
                return g[0], g[1], g[2]
    return None


def main():
    recs = []
    # Primærhelsetjeneste (centros de salud og consultorios locales) – alle er en del av det offentlige systemet
    for r in rows("2026_C_Catal_Centros_AP.xlsx", "Catálogo - 2026"):
        if not r.get("SIAP_CENTROS.NOMBRE"):
            continue
        tipo = "Centro de Salud" if "SALUD" in str(r["TIPOCENTRO"]) else "Consultorio local"
        recs.append({"src": "ap", "name": tipo + " " + pretty(re.sub(r"^(C\.?S\.?I\.?|C\.?S\.?|C\.?L\.?|CONSULTORIO LOCAL|CONSULTORIO|CENTRO DE SALUD|CENTRO SALUD)\s+", "", str(r["SIAP_CENTROS.NOMBRE"]).strip())), "raw": r["SIAP_CENTROS.NOMBRE"],
                     "addr": pretty(clean_addr(r["DIRECCION"])), "cp": str(r["CP"] or ""), "loc": pretty(r["LOCALIDAD"]),
                     "muni": r["MUNICIPIO"], "prov": pretty(r["SIAP_PROVINCIAS.NOMBRE"]), "tel": str(r["TELEFONO"] or ""),
                     "sec": "pub", "kind": "c", "urg": 0})
    # Legevakter utenfor sykehus (PAC, SUAP, CAC …)
    for r in rows("2026_C_Catal_disp_urg.xlsx", "Catálogo - 2026"):
        tel = re.sub(r"_.*", "", str(r.get("C_TELEFONO") or ""))
        tel = tel if re.search(r"\d{9}", tel) else ""
        recs.append({"src": "urg", "name": pretty(r["T_NOMBRE"]), "raw": r["T_UBICACION"], "ubic": pretty(r["T_UBICACION"]),
                     "addr": pretty(clean_addr(r["T_DIRECCION"])), "cp": str(r["C_CODPOSTAL"] or ""), "loc": pretty(r["T_LOCALIDAD"]),
                     "muni": r["MUNICIPIO"], "prov": pretty(r["SIAP_PROVINCIAS.NOMBRE"]), "tel": tel,
                     "hor": str(r.get("T_HORARIO") or "").strip(), "sec": "pub", "kind": "c", "urg": 1})
    # Sykehus (Catálogo Nacional de Hospitales) med offisiell eierform
    for r in rows("CNH_2025.xlsx", "DIRECTORIO DE HOSPITALES"):
        clase, dep = str(r["Cód. Clase de Centro"]), str(r["Dependencia Funcional"] or "")
        if clase not in ("C11", "C12") or "Mútua" in dep or "Mutua" in dep or "Penitenciari" in str(r["Nombre Centro"]):
            continue
        priv = dep.startswith("Privad") or dep.startswith("Organizaciones No Gub")
        recs.append({"src": "h", "name": r["Nombre Centro"], "raw": r["Nombre Centro"], "addr": pretty(clean_addr(r["Dirección"])),
                     "cp": str(r["Código Postal"] or ""), "loc": r["Municipio"], "muni": r["Municipio"], "prov": r["Provincia"],
                     "tel": str(r["Teléfono"] or ""), "sec": "priv" if priv else "pub", "kind": "h",
                     "urg": 1 if (not priv and clase == "C11") else 0, "dep": dep})

    def job(rec):
        g = locate(rec["addr"], rec["cp"], rec["loc"], rec["muni"], rec["prov"])
        if g:
            rec["lat"], rec["lon"], rec["prec"] = g
        a = geocode(str(rec["muni"]).split("/")[0])
        if a:
            rec["anchor"] = [a[0], a[1]]
        return rec

    with ThreadPoolExecutor(4) as ex:
        for i, _ in enumerate(ex.map(job, recs)):
            if i % 1000 == 0:
                print(i, "/", len(recs), flush=True)
                json.dump(cache, open(CACHE_F, "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(cache, open(CACHE_F, "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(recs, open("data/oficial.json", "w"), ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    print(Counter((r["src"], "lat" in r) for r in recs))


if __name__ == "__main__":
    main()
