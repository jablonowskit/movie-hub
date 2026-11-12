# FlixMomo players — test jakości streamu (2026-10-28)

Źródło listy: [flixmomo.us/play/movie/1283515](https://flixmomo.us/play/movie/1283515) (film **Verity**, TMDB `1283515`).

Cel: nie powtarzać ręcznego / CDP „klikaj i zgaduj” — poniżej wynik jednego przebiegu CDP (Edge `:9222`), żeby przy dodawaniu playerów brać tylko te z **twardym dowodem HQ**.

## Metoda

Dla każdego embedu (nowe vs nasza lista + baseline CineSrc):

1. `Page.navigate` → czekaj ~5.5 s
2. UI: `<video>`, tekst/opcje z `1080p` / `4K` / `720p`
3. Network: requesty z `1080` / `2160` / `4k` / `720` w URL (odrzucamy `data:image…` — fałszywe trafienia)

**HQ (w tym teście, v1)** = realny stream z **1080p+ w URL/playliście** (lub UI 1080p + `<video>`).  
**Uwaga (2026-10-28):** sama rozdzielczość **nie** świadczy o jakości — liczy się **bitrate** (`BANDWIDTH` w master HLS / faktyczne MB/s segmentów). Np. CineSrc „1080p” przy Verity ma tylko ~3 Mbps (patrz niżej). Przy kolejnych decyzjach „dodać player” brać bitrate, nie samą etykietę 1080p.

Nasza lista wtedy: CineSrc, Cinezo, VidSrc, VidLink, VidZee, FlaxMovies.

## Werdykt (skrót)

| Player | Embed (movie) | HQ? | Dowód / uwagi |
|---|---|---|---|
| **CineSrc** (baseline) | `cinesrc.st/embed/movie/{id}` | **tak** | `<video>` + HLS `…/1080p/…` |
| **MoviesAPI** | `moviesapi.to/movie/{id}` | **tak** | UI `Quality 1080p (Auto)` + `<video>` + segmenty |
| **VixSrc** | `vixsrc.to/movie/{id}` | **tak** | playlist `rendition=1080p` (+ 720p) |
| **Filmu** | `embed.filmu.in/movie/{id}` | **tak** | DASH/HLS path `…_1080_h265_…` + `<video>` |
| PeeStream | `peestream.in/embed/?tmdbId={id}&type=movie` | **prawdopodobnie** | `<video>` + serwery `YP-HDBOX` / `FULLHD`; brak 1080 w URL w tym przebiegu |
| VidFast | `vidfast.vc/movie/{id}` | **słabe** | UI „4k”, ale w net tylko `4k.png` — bez segmentów 4K/1080 |
| VidEasy | `player.videasy.net` → `player.videasy.to` | **słabe** | brak `<video>` w oknie; netHQ = głównie `data:` |
| VidCore | `vidcore.net/movie/{id}` | **niejasne** | `<video>`, brak etykiety/URL 1080 |
| VidSrc.su | `vidsrc.su/movie/{id}` | **niejasne** | `<video>`, brak 1080 w URL |
| 2Embed | `2embed.cc/embed/{id}` | **nie** | brak video/HQ w tym przebiegu (`HDToday` w UI) |
| PrimeSrc | `primesrc.me/embed/movie?tmdb={id}` | **nie** | brak video/HQ |
| MultiEmbed | `multiembed.mov/?video_id={id}&tmdb=1` | **nie** | title jak PrimeSrc; brak video/HQ |
| AutoEmbed | `player.autoembed.cc/embed/movie/{id}` | **nie** | brak video; netHQ = `data:` |
| VAPlayer | `vaplayer.ru/embed/movie/{id}` | **nie** | brak video/HQ |
| Vares | `vares.app/movie/{id}` | **nie** | brak video; netHQ = `data:` |
| VidGod | `vidgod.net/movie/{id}` | **nie** | j.w. |
| VidSrc.me | `vidsrc.me/embed/movie?tmdb={id}` | **nie** | pusto w tym przebiegu |
| **111Movies** | `111movies.com/movie/{id}` | **martwy** | domena na sprzedaż (Sedo) |
| **VidBolt** | `vidbolt.xyz/movie/{id}` | **martwy** | HTTP 404 |
| **VidZee** | `player.vidzee.wtf/embed/…` | **down** | Cloudflare **522** (także flixmomo / `/v2/embed`); adres **bez zmian** |

## Kandydaci do dodania (tylko HQ)

Zgodnie z regułą „tylko stream wysokiej jakości”:

1. **MoviesAPI** — `https://moviesapi.to/movie/{id}` (TV: do potwierdzenia osobno)
2. **VixSrc** — `https://vixsrc.to/movie/{id}`
3. **Filmu** — `https://embed.filmu.in/movie/{id}`
4. Opcjonalnie **PeeStream** — po potwierdzeniu 1080 w network albo subiektywnym teście oka

Nie dodawać na podstawie samego marketingu / ikony 4K (VidFast) ani domen „for sale” / 404.

## Pełna lista serwerów flixmomo (30) + URL movie

Zebrane kliknięciem przycisków na stronie play (ten sam film):

| Nazwa | iframe src |
|---|---|
| Cinezo | `https://player.cinezo.live/embed/movie/1283515` |
| CineSrc | `https://cinesrc.st/embed/movie/1283515` |
| PeeStream | `https://peestream.in/embed/?tmdbId=1283515&type=movie` |
| FlaxMovies | `https://flaxmovies.xyz/embed/movie/1283515` |
| MoviesAPI | `https://moviesapi.to/movie/1283515` |
| VidLink | `https://vidlink.pro/movie/1283515` |
| VidSrc Embed | `https://vidsrc-embed.ru/embed/movie/tt32261958` (IMDb) |
| VidEasy | `https://player.videasy.net/movie/1283515` |
| 111Movies | `https://111movies.com/movie/1283515` |
| VidZee | `https://player.vidzee.wtf/embed/movie/1283515` |
| VidSrc | `https://vidsrc.to/embed/movie/1283515` |
| 2Embed | `https://www.2embed.cc/embed/1283515` |
| Mapple | `https://mapple.uk/watch/movie/1283515` |
| PrimeSrc | `https://primesrc.me/embed/movie?tmdb=1283515` |
| MultiEmbed | `https://multiembed.mov/?video_id=1283515&tmdb=1` |
| AutoEmbed | `https://player.autoembed.cc/embed/movie/1283515` |
| VixSrc | `https://vixsrc.to/movie/1283515` |
| VidLove | `https://player.vidlove.cc/embed/movie/1283515` |
| VidFast | `https://vidfast.vc/movie/1283515` |
| Filmu | `https://embed.filmu.in/movie/1283515` |
| VidCore | `https://vidcore.net/movie/1283515?theme=%23E50914` |
| VAPlayer | `https://vaplayer.ru/embed/movie/1283515?skin=netflix&color=ff0000` |
| Vares | `https://vares.app/movie/1283515` |
| VidKing | `https://www.vidking.net/embed/movie/1283515` |
| VidBolt | `https://vidbolt.xyz/movie/1283515` |
| VidNest | `https://vidnest.fun/movie/1283515` |
| VidSrc.su | `https://vidsrc.su/movie/1283515?…` |
| VidGod | `https://vidgod.net/movie/1283515` |
| VidSrc.me | `https://vidsrc.me/embed/movie?tmdb=1283515` |
| 1Embed | `https://1embed.cc/embed/movie/1283515` |

## Bitrate (BANDWIDTH) — Verity `1283515`, CDP 2026-10-28

Źródło: master HLS `#EXT-X-STREAM-INF:BANDWIDTH=…` albo DASH `bandwidth="…"`.  
`null` = w ~9 s nie złapano playlisty (iframe/WASM/klik / inny protokół) — **brak dowodu**, nie „0 Mbps”.

### Ranking max wariantu (wyżej = lepiej na papierze)

| Player | max Mbit/s | max RESOLUTION | inne warianty | display `<video>` |
|---|---:|---|---|---|
| **VidSrc.su** | **5.76** | 1920×1080 | 3.14@720p, 0.79@360p | 1920×1080 |
| **Filmu** | **5.0** | 1920×1080 | 4.77@1920×800, 3.0@720p, … | 0×0 (w oknie testu) |
| **VixSrc** | **4.5** | 1920×1080 | 1.8@720p, 0.72@360p | 0×0 |
| **CineSrc** | **2.99** | 1920×1080 (NAME 1080p) | 1.33@720p | 1920×800 |
| **Cinezo** | **2.2** | 2592×1080 (DASH) | 1.0@1728×720, 0.5@1152×480 | 0×0 |
| **MoviesAPI** | **1.86** | 1920×800 | 0.88@1280×532 | 1920×800 |
| VidSrc / VidLink / FlaxMovies / PeeStream / VidFast / VidEasy / VidCore / AutoEmbed / PrimeSrc / 2Embed | — | — | brak złapanej playlisty | — |

### CineSrc (szczegół)

| NAME | RESOLUTION | BANDWIDTH | ≈ Mbit/s |
|---|---|---|---|
| 1080p | 1920×1080 | 2 992 000 | ~3.0 |
| 720p | 1280×720 | 1 328 000 | ~1.3 |

### Wniosek do dodawania

- Sama „1080p” w UI/URL **nie** wystarczy — **MoviesAPI** ma 1080-szerokie klatki przy tylko **~1.9 Mbps** (słabiej niż CineSrc).
- Najwyższy zmierzony bitrate w tej próbce: **VidSrc.su (~5.8)**, **Filmu (~5)**, **VixSrc (~4.5)** — powyżej CineSrc (~3).
- Cinezo ultrawide 2592×1080 przy **~2.2 Mbps** też jest raczej lekki.
- Lista w `movie-server/players.py` + `panscan-zoom-video.user.js` (od 2026-10-28):  
  **VidSrc.su → Filmu → VixSrc → CineSrc → Cinezo → MoviesAPI → VidSrc** (`vidsrc.to`, na końcu — pokrycie katalogu mimo słabszej jakości).  
  Usunięte: VidLink, VidZee, FlaxMovies.

## Uwagi

- Test **jednego** tytułu; inny film może mieć inne jakości / brak źródeł.
- URL TV dla nowych HQ **nie** był weryfikowany w tym przebiegu — przed wrzuceniem do `players.py` sprawdzić wzorzec na flixmomo `/play/tv/…`.
- Sama etykieta „1080p” w UI bywa marketingiem (wcześniej VidSrc `/info`); tu wymagamy też network / video.
- Powiązane: [2026-10-28-movie-server-cdp-timings.md](./2026-10-28-movie-server-cdp-timings.md) (czasy `/players`, CineSrc TV `season`/`episode`).
