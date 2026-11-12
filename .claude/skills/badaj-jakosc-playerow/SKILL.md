---
name: badaj-jakosc-playerow
description: Zmierz jakość embedów (bitrate HLS/DASH, nie sama rozdzielczość) przez CDP Edge :9222 i zapisz wnioski. Użyj przed dodaniem nowych playerów do movie-server/players.py albo panscan-zoom-video.user.js.
---

# Badanie jakości playerów (bitrate)

**Rozdzielczość (1080p) ≠ jakość.** Decyzje o liście playerów bierz z
`BANDWIDTH` w master HLS / `bandwidth` w DASH, nie z etykiety UI.

Źródło prawdy z sesji 2026-10-28 (Verity TMDB `1283515`):
[`docs/2026-10-28-flixmomo-player-quality.md`](../../../docs/2026-10-28-flixmomo-player-quality.md).

## Metoda (CDP Edge `127.0.0.1:9222`)

1. Otwórz embed (albo kliknij serwer na flixmomo → iframe `src`).
2. Złap requesty `*.m3u8` / `*.mpd` / `manifest`.
3. `Network.getResponseBody` → parsuj `#EXT-X-STREAM-INF:BANDWIDTH=…,RESOLUTION=…`
   albo DASH `bandwidth="…"`.
4. Odrzuć fałszywe „HQ” z `data:image…` w URL.

Przykład CineSrc (ten film): 1080p przy **~3.0 Mbit/s**; MoviesAPI „1080”
przy **~1.9 Mbit/s** — słabiej mimo tej samej szerokości klatki.

## Lista w kodzie (kolejność = max bitrate, ten test)

`movie-server/players.py` + `panscan-zoom-video.user.js` (trzymaj w sync):

1. VidSrc.su (~5.8)  
2. Filmu (~5.0)  
3. VixSrc (~4.5)  
4. CineSrc (~3.0)  
5. Cinezo (~2.2 DASH ultrawide)  
6. MoviesAPI (~1.9)  
7. VidSrc / vidsrc.to (bitrate niezmierzony w teście; na końcu — duże pokrycie)

Brak złapanej playlisty w limicie czasu = **brak dowodu**, nie „0 Mbps”.

## Flixmomo jako katalog URL-i

`https://flixmomo.us/play/movie/{tmdb}` — klikaj przyciski serwerów, zbieraj
`iframe.src`. TV: potwierdź wzorzec HTTP (często `/tv/{id}/{s}/{e}`).

## Po zmianie listy

1. Sync `players.py` ↔ `getPlayers()` w userscripcie + `syncPlayerIdx`.
2. Podbij `@version` userscriptu.
3. Skill `wdroz-movie-server` (w tym plik `.user.js` na routerze).
4. Skill `wgraj-userscript-telefon` albo desktop `zainstaluj-w-tampermonkey`.
