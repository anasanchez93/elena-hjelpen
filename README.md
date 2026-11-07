# Elena hjelpen

App (PWA) for nordmenn i Spania: innlegg fra Instagram, råd, spansk ordliste, spørsmål og timebestilling hos sykepleier Elena.

- Endre timer, tjenester, innlegg og råd øverst i `<script>` i `index.html` (CONFIG, POSTS, GUIDES, WORDS).
- Etter endringer: bytt `CACHE`-versjonen i `sw.js` (v1 → v2) så telefonene henter den nye versjonen.

## Timebestilling (Supabase)
- Bestillinger lagres i Supabase-prosjektet **elena-hjelpen** (EU, Paris), tabell `bookings`.
- Elenas panel: `admin.html` (innlogging med elenahjelpen@gmail.com).
- Arbeidstiden står **to steder**: `CONFIG.schedule` i `index.html` og funksjonen `validate_booking()` i databasen. Endres den, må begge oppdateres.
- Bestillinger slettes automatisk 12 måneder etter timen (pg_cron).
