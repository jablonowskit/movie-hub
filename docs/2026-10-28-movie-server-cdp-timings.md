# movie-server — czasy z testów CDP (2026-10-28)

Środowisko: lokalny `movie-server` na `http://127.0.0.1:9000/`, pomiar przez CDP Edge (`127.0.0.1:9222`).

## Wyszukiwanie „x files”

| Metryka | Czas |
|---|---|
| `GET /search?q=x%20files` (Performance API / CDP Network) | ~58 ms |
| UI do statusu „20 wyników” | ~104 ms |
| to samo API przez curl | ~40–53 ms |

Pierwsze wyniki m.in.: *The X-Files*, *The X-Files: I Want to Believe*.

## Klik pierwszego wyniku (The X-Files, TV id 4087)

Serial → panel sezon/odcinek (bez `/players` na tym kroku).

| Metryka | Czas |
|---|---|
| UI → nagłówek + selecty | ~82 ms |
| `GET /tv/4087` | ~40 ms (CDP); curl ~37 ms |
| `GET /tv/4087/season/1` | ~63 ms (CDP); curl ~68 ms |

## Klik „Pokaż playery” (S1E1 → `/players/tv/4087/1/1`)

| Metryka | Czas |
|---|---|
| UI → lista playerów | ~21.8 s |
| `GET /players/tv/4087/1/1` (CDP) | ~21.2 s |
| to samo curl (kolejne wywołanie) | ~15.0 s |

Bottleneck: zewnętrzne probe napisów w `players_extra` (CineSrc / Cinezo / VidZee), nie sam klik UI.

Badge przy tym teście (przed poprawką CineSrc TV): CineSrc **PL 0**, Cinezo **PL 2**, VidSrc, VidLink, VidZee, FlaxMovies.

## Uwaga: CineSrc PL przy TV

Sam `POST …/subtitles/search` z `{"tmdbId": 4087}` → 0 wyników. Z `{"tmdbId": 4087, "season": 1, "episode": 1}` → **11** ścieżek `pl` (sprawdzone 2026-10-28). W playerze napisy PL są — badge PL 0 wynikał z braku `season`/`episode` w body.
