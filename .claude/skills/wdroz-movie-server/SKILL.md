---
name: wdroz-movie-server
description: Wdróż lub zaktualizuj movie-server na routerze OpenWrt (japa55.japa, port 9000). Użyj po każdej zmianie w movie-server/, gdy użytkownik ma zobaczyć efekt pod http://192.168.55.1:9000/ — lokalne pliki same się tam nie pojawią.
---

# Wdrożenie movie-server na router

Użytkownik ogląda serwer pod `http://192.168.55.1:9000/` (LAN routera).
Zmiany w `movie-server/` na dysku lokalnym **nie działają**, dopóki nie
skopiujesz plików na router (i przy `.py` — nie przeładujesz procesu).

## Docelowe miejsce

| | |
|---|---|
| Host SSH | `japa55.japa` |
| Katalog | `/mnt/sd/movie-server/` |
| Port | `9000` |
| Python | 3.7 (`python3` → `/mnt/sd/usr/bin/python3.7`) |
| URL LAN | `http://192.168.55.1:9000/` |
| Pidfile | `/tmp/server.py.pid` |
| Keepalive | cron co 1 min: `/mnt/sd/movie-server/run_skrypt.sh server.py 9000` |

Kod **stdlib only** (`urllib`, `http.server`, `json`, `re`) — bez pip.

## Krok 1: skopiuj zmienione pliki

Na Windows (PowerShell) — UTF-8, bez `scp`:

```powershell
Get-Content -Raw -Encoding utf8 "d:\github\skryptyjs\movie-server\server.py" | ssh japa55.japa "cat > /mnt/sd/movie-server/server.py"
```

Typowe ścieżki:

- `server.py`, `tmdb.py`, `tmdb_key.py`, `players.py`, `metacritic.py`, `player_info.py`
  → `/mnt/sd/movie-server/<plik>`
- `static/index.html` → `/mnt/sd/movie-server/static/index.html`
- `panscan-zoom-video.user.js` (katalog główny repo) →
  `/mnt/sd/movie-server/panscan-zoom-video.user.js`  
  Endpoint: `GET /panscan-zoom-video.user.js` (Tampermonkey `@updateURL` /
  `@downloadURL` = `http://192.168.55.1:9000/panscan-zoom-video.user.js`).  
  Po zmianie skryptu **zawsze** skopiuj ten plik na router (nawet bez restartu
  procesu, jeśli nie ruszałeś `server.py` — handler czyta plik z dysku).

Skopiuj **wszystkie** zmienione pliki z danej sesji.

Weryfikacja userscriptu:

```powershell
ssh japa55.japa 'wget -qO- http://127.0.0.1:9000/panscan-zoom-video.user.js | head -c 200'
```

## Krok 2: przeładuj proces tylko gdy zmieniłeś `.py`

### Tylko HTML / static

`index.html` jest czytany z dysku przy każdym `GET /` (`Cache-Control: no-store`).
**Nie zabijaj procesu.** Poproś użytkownika o Ctrl+F5.

### Zmiana `*.py` — bezpieczny restart (preferowany)

Cron i tak podnosi `server.py` co minutę przez `run_skrypt.sh`. Nie uruchamiaj
drugiego `python3 server.py` ręcznie „obok” — dostaniesz `Address in use` i wpisy
`server.py nie zyje` w `/mnt/sd/movie-server/events.log`.

**Zrób tak:** zabij wyłącznie PID z pidfile, usuń pidfile, poczekaj na cron
(albo od razu odpal `run_skrypt.sh`):

```powershell
ssh japa55.japa "PID=`$(cat /tmp/server.py.pid 2>/dev/null); if [ -n `"`$PID`" ]; then kill `$PID; fi; rm -f /tmp/server.py.pid; /mnt/sd/movie-server/run_skrypt.sh server.py 9000"
```

Uwaga PowerShell: w podwójnych cudzysłowach `$()` i `$PID` są rozwijane lokalnie.
Albo escape jak wyżej (` `$ `), albo **pojedyncze cudzysłowy** wokół całej
komendzy zdalnej:

```powershell
ssh japa55.japa 'PID=$(cat /tmp/server.py.pid 2>/dev/null); if [ -n "$PID" ]; then kill $PID; fi; rm -f /tmp/server.py.pid; /mnt/sd/movie-server/run_skrypt.sh server.py 9000'
```

Wariant „tylko kill + czekaj na cron” (do ~60 s):

```powershell
ssh japa55.japa 'PID=$(cat /tmp/server.py.pid 2>/dev/null); if [ -n "$PID" ]; then kill $PID; fi; rm -f /tmp/server.py.pid'
```

## Krok 3: weryfikacja

```powershell
ssh japa55.japa 'ps w | grep server.py | grep -v grep'
ssh japa55.japa 'wget -qO- http://127.0.0.1:9000/ | head -c 200'
ssh japa55.japa 'wget -qO- http://127.0.0.1:9000/trending | head -c 200'
```

Nowy endpoint — sprawdź `wget`-em. Log dnia: `/tmp/server.py_YYYYMMDD.log`.
Zdarzenia padnięć: `/mnt/sd/movie-server/events.log`.

## Czego NIGDY nie robić

- **`reboot` / restart całego routera** — wdrażasz tylko proces `server.py`.
  Cotygodniowy restart routera to osobna sprawa (`clean_reboot.sh`, niedziela 6:00),
  nie część wdrożenia movie-server.
- `kill` po `ps | grep server.py` — łapie też linię `ash -c ... server.py` /
  crona; przy złym escape PowerShell potrafi wstawić lokalny PID.
- Ręczne `python3 -u server.py 9000 &` **równolegle** z żywym procesem / cronem
  → `OSError: Address in use`.
- `nohup` (nie ma na BusyBox), `pip install`, biblioteki spoza stdlib.
- Zakładania, że lokalny `python server.py` = to, co w LAN na `:9000`.

## Kiedy używać

- Po edycji czegokolwiek w `movie-server/`, zanim powiesz „odśwież”.
- Gdy użytkownik nie widzi zmian pod `192.168.55.1:9000`.
