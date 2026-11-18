# Elena hjelpen

App (PWA) for nordmenn i Spania: innlegg fra Instagram, råd, spansk ordliste, spørsmål og timebestilling hos sykepleier Elena.

- Endre timer, tjenester, innlegg og råd øverst i `<script>` i `index.html` (CONFIG, POSTS, GUIDES, WORDS).
- Etter endringer: bytt `CACHE`-versjonen i `sw.js` (v1 → v2) så telefonene henter den nye versjonen.

## Timebestilling (Supabase)
- Bestillinger lagres i Supabase-prosjektet **elena-hjelpen** (EU, Paris), tabell `bookings`.
- Elenas panel: `admin.html` (innlogging med elenahjelpen@gmail.com).
- Arbeidstiden står **to steder**: `CONFIG.schedule` i `index.html` og funksjonen `validate_booking()` i databasen. Endres den, må begge oppdateres.
- Bestillinger slettes automatisk 12 måneder etter timen (pg_cron).
- Pasientkontoer: «Min side» i appen (Supabase Auth). Pasienter ser og avbestiller egne timer (`my_bookings`, `cancel_my_booking`).
- E-postvarsler: Edge Function `notify` (Gmail SMTP, port 465) kalles av databasen ved ny/bekreftet/avlyst time. Krever secret `GMAIL_APP_PASSWORD`.
- `vendor/supabase-2.119.0.js` er supabase-js (UMD) lagt inn lokalt.

## Innlegg fra panelet
- Fanen «📸 Publicaciones» i `admin.html` laster opp bilder/reels til Supabase Storage (bøtte `posts`) og lagrer dem i tabellen `posts`.
- `index.html` henter publiserte innlegg derfra og viser dem først, foran de faste innleggene i `POSTS`.
- Databaseoppsettet står i `posts.sql` (kjøres én gang i SQL Editor).

## Kart over helsetilbud
- Fanen «Kart» viser sykehus og helsesentre i hele Spania (offentlige og private) med Leaflet (`vendor/leaflet/`) og kartfliser fra OpenStreetMap.
- Offentlige helsesentre, legevakter og sykehus (med offentlig/privat) kommer fra Ministerio de Sanidad sine offisielle kataloger (`data/offisiell/`), geokodet med CartoCiudad (`tools/official.py`, cache i `data/geocache.json`). Private klinikker og tannleger kommer fra OpenStreetMap.
- Dataene ligger i `data/helse.json`. GitHub Action `osm.yml` henter dem fra OpenStreetMap (Geofabrik) den 1. i hver måned og kjører `tools/build_helse.py`, som sorterer i offentlig/privat.
- Adressesøket bruker Nominatim (OpenStreetMap), maks ett søk per sekund, kun ved trykk på «Søk».
