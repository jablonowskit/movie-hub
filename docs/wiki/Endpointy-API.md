# Endpointy API

Wszystkie odpowiedzi to JSON, poza `/` (HTML), `/panscan-zoom-video.user.js` (JS) i przekierowaniami `/watch/*` (302).

| Metoda i ścieżka | Parametry | Opis |
|------------------|-----------|------|
| `GET /search` | `q` (wymagany) | Wyszukiwanie multi w TMDB (filmy, seriale, osoby). |
| `GET /trending` | — | Trending filmów i seriali na dziś, pierwsza strona. Odpowiedź: `{"movies": …, "tv": …}`. |
| `GET /trending/movie` | `page` | Kolejna strona trendingu filmów. |
| `GET /trending/tv` | `page` | Kolejna strona trendingu seriali. |
| `GET /popular/<kategoria>` | `page` | Kategorie: `streaming`, `w_tv`, `for_rent`, `w_kinach`. |
| `GET /movie/<id>` | — | Szczegóły filmu (opis po polsku). |
| `GET /movie/<id>/quality` | — | `{"quality": "HD"}`, `"CAM"` albo `null`. |
| `GET /movie/<id>/metacritic` | `title`, `year`, `alt` (opcjonalne) | `{"metacritic_user": …}`. Nie jest to Metascore. |
| `GET /tv/<id>` | — | Szczegóły serialu i lista sezonów. |
| `GET /tv/<id>/season/<n>` | — | Szczegóły sezonu z datami odcinków. |
| `GET /players/movie/<id>` | — | Lista embedów dla filmu. |
| `GET /players/tv/<id>/<s>/<e>` | — | Lista embedów dla odcinka. |
| `GET /watch/movie/<id>` | — | 302 do pierwszego playera. |
| `GET /watch/tv/<id>/<s>/<e>` | — | 302 do pierwszego playera. |

## Paginacja

`page` działa dla trendingu i popularnych kategorii. Zakres to 1–500 (limit TMDB). Wartość spoza zakresu jest przycinana, a niepoprawna traktowana jest jako 1.

Przykład:

```bash
curl "http://localhost:9000/popular/streaming?page=2"
```
