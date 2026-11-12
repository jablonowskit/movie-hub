# skryptyjs

Userscripty Tampermonkey oraz lekki serwer **movie-server** do szukania filmów i seriali oraz otwierania embedów playerów. Działa na desktopie i na telefonie (Firefox Android).

Szczegóły techniczne i API: [wiki](https://github.com/jablonowskit/movie-hub/wiki).

## Co tu jest

| Część | Opis |
|-------|------|
| `*.user.js` | Samodzielne skrypty Tampermonkey wstrzykiwane w strony (jeden plik = jeden skrypt). |
| `movie-server/` | Serwer HTTP tylko na bibliotece standardowej Pythona: TMDB → lista tytułów → linki do playerów. |
| `docs/` | Raporty z pomiarów (jakość playerów, czasy CDP). |
| `tools/` | Narzędzia pomocnicze, np. WebDriver BiDi do testów userscriptów. |
| `.claude/skills/` | Procedury dla agenta Claude Code (ADB, wdrożenie na router, instalacja w Tampermonkey). |

## movie-server

Wyszukiwarka filmów i seriali:

- trending (filmy i seriale) oraz „What's Popular": Streaming, W TV, For Rent, W kinach,
- przycisk **Następne ▶** w każdej sekcji — dokłada kolejną stronę wyników bez duplikatów,
- wyszukiwanie po tytule (TMDB),
- wybór sezonu i odcinka,
- lista embedów playerów (VidSrc, Filmu, VixSrc, CineSrc i inne),
- filtr jakości: **HD** vs **CAM** (także tytuły przed premierą),
- ocena Metacritic User Score obok ocen TMDB.

### Uruchomienie lokalnie

```bash
cd movie-server
python server.py 9000
# → http://localhost:9000/
```

Docelowo serwer działa na routerze OpenWrt w sieci LAN: `http://<adres-routera>:9000/`.

### Endpointy

| Ścieżka | Opis |
|---------|------|
| `/` | Interfejs użytkownika. |
| `/search?q=…` | Wyszukiwanie multi (filmy, seriale, osoby). |
| `/trending` | Trending filmów i seriali na dziś (pierwsza strona). |
| `/trending/movie?page=N`, `/trending/tv?page=N` | Kolejne strony trendingu. |
| `/popular/<kategoria>?page=N` | Kategorie: `streaming`, `w_tv`, `for_rent`, `w_kinach`. |
| `/movie/<id>`, `/tv/<id>`, `/tv/<id>/season/<n>` | Szczegóły z TMDB (opisy po polsku). |
| `/movie/<id>/quality` | Jakość filmu: `HD`, `CAM` albo brak. |
| `/movie/<id>/metacritic` | Metacritic User Score. |
| `/players/movie/<id>`, `/players/tv/<id>/<s>/<e>` | Lista embedów dla filmu lub odcinka. |
| `/watch/movie/<id>`, `/watch/tv/<id>/<s>/<e>` | Przekierowanie 302 do pierwszego playera. |
| `/panscan-zoom-video.user.js` | Userscript do auto-aktualizacji w Tampermonkey. |

Parametr `page` jest ograniczony do zakresu 1–500. Zły lub brakujący parametr traktowany jest jako stronę 1.

## Userscripty

- **[panscan-zoom-video.user.js](panscan-zoom-video.user.js)**: panscan i zoom wideo, pasy letterbox, przełączanie playerów.

Opis każdego skryptu znajduje się w bloku `@description` w pliku. Osobnych plików `.md` dla skryptów nie prowadzimy.

Instalacja: Tampermonkey (Firefox desktop lub Android). Na routerze skrypt jest serwowany pod `/panscan-zoom-video.user.js`, więc działa auto-update przez `@updateURL`.

## Wymagania

- **movie-server:** Python 3.7 lub nowszy. Celowo tylko biblioteka standardowa, bo działa też na OpenWrt.
- **Userscripty:** Tampermonkey i nowoczesna przeglądarka.
- **Klucz TMDB:** pobierany w czasie działania z publicznych źródeł (`movie-server/tmdb_key.py`). W repo nie ma sekretów.

## Struktura

```
movie-hub/
├── panscan-zoom-video.user.js
├── movie-server/
│   ├── server.py          # HTTP API i serwowanie interfejsu
│   ├── tmdb.py            # TMDB: trending, popular, search, szczegóły, jakość
│   ├── players.py         # lista embedów
│   ├── metacritic.py      # Metacritic User Score
│   ├── tmdb_key.py        # pobieranie klucza TMDB
│   └── static/index.html  # interfejs (mobile-first)
├── docs/                  # raporty z pomiarów
├── tools/                 # narzędzia pomocnicze (bidi.js)
└── .claude/skills/        # procedury agenta
```

## Licencja

W repo nie ma jeszcze pliku `LICENSE`, więc licencja nie jest ustalona.

Embedy playerów należą do ich operatorów. Projekt tylko składa linki do nich.
