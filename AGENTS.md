# Zasady pracy w repozytorium

## Zakazane sformułowania

- Nie używaj słów/zwrotów: "nie zrobię", "nie wolno", "odmawiam", "nie będę".

## Dobór modelu / subagentów

- Do prostych, jednoznacznych zadań (wyszukiwanie, drobne poprawki, mechaniczne
  zmiany) używaj prostszych/tańszych modeli LLM i subagentów.
- Do zadań złożonych (wieloetapowe zmiany, analiza architektury, trudne decyzje
  projektowe) używaj bardziej zaawansowanych modeli.
- Deleguj do subagenta tylko wtedy, gdy zadanie **nie wymaga** kontekstu bieżącej
  rozmowy. Jeśli praca zależy od tego, co już ustalono w tej sesji (zdiagnozowany
  błąd, decyzje z ostatnich wiadomości), subagent zaczyna bez tego kontekstu i
  albo zgaduje, albo trzeba mu go w całości powtórzyć — wtedy taniej zrobić to
  samemu.

## Weryfikacja rzeczywistości przed kodem

- Zewnętrzne API/dane sprawdzaj realnym wywołaniem (curl, DevTools Network) zanim
  napiszesz kod je obsługujący — nie zgaduj kształtu odpowiedzi.
- Odpowiedzi z realnych wywołań nadają się wprost na fixture'y testowe.

## Kodowanie i pliki

- Pliki tekstowe i kod: UTF-8.
- Nigdy nie zapisuj sekretów (tokeny, hasła, klucze API, ciasteczka sesji) w
  logach, kodzie ani repo.

## Czym jest ten projekt

Zbiór userscriptów JavaScript uruchamianych przez Tampermonkey w przeglądarce
(desktop i Firefox na Androidzie). Każdy skrypt to samodzielny plik `.user.js`
wstrzykiwany w konkretne strony internetowe.

W repo jest też `movie-server/` — lekki serwer HTTP (stdlib Python) z listą
filmów/playerów, docelowo na routerze OpenWrt (patrz sekcja poniżej).

## Procedury (skille)

Powtarzalne procedury dla tego projektu są opisane w `.claude/skills/<nazwa>/SKILL.md`
(katalog `.cursor/skills/` to junction na to samo miejsce — jedna treść, dwie
nazwy narzędzi). Przeczytaj je zamiast odkrywać te procedury na nowo:

- `polacz-telefon` — łączenie z telefonem Android przez ADB (co się da i czego
  nie da się sprawdzić bez roota).
- `steruj-telefonem` — sterowanie telefonem przez ADB (tap, swipe, keyeventy,
  tekst, zrzuty ekranu, otwieranie URL i restart apek).
- `testuj-userscript-bidi` — automatyczne testowanie userscriptu przez
  WebDriver BiDi (`tools/bidi.js`), bez ręcznego klikania w przeglądarce.
- `zainstaluj-w-tampermonkey` — instalacja/aktualizacja pliku `.user.js` w
  Tampermonkey na **desktopie** (Firefox).
- `wgraj-userscript-telefon` — instalacja/aktualizacja tego samego skryptu na
  **telefonie** (Firefox Android + ADB; URL z routera `:9000`).
- `wdroz-movie-server` — wdrożenie/aktualizacja `movie-server/` na routerze
  (`japa55.japa`, port 9000 / `http://192.168.55.1:9000/`), w tym plik
  userscriptu pod `/panscan-zoom-video.user.js`.
- `badaj-jakosc-playerow` — pomiar bitrate embedów (CDP) przed zmianą listy
  playerów; rozdzielczość sama w sobie nie wystarcza.

## Telefon

- Telefon bywa dostępny przez ADB (USB + debugowanie) — używaj skilli
  `polacz-telefon` / `steruj-telefonem`, zamiast zakładać brak dostępu.
- Listy/kodu skryptów Tampermonkey z Firefoksa na telefonie ADB bez roota nie
  odczyta — to trzeba dostać od użytkownika (zrzut ekranu, eksport z Dashboard →
  Utilities → Export, albo wklejony kod) albo poprosić o ręczny test po zmianie.
- Aktualizacja skryptu na telefonie: skill `wgraj-userscript-telefon` (URL
  `http://192.168.55.1:9000/panscan-zoom-video.user.js`).

## Struktura repo

- Jeden skrypt = jeden plik `.user.js` (w katalogu głównym).
- Dokumentacja skryptu = opis w bloku `@description`, bez osobnych `.md` per skrypt.
- `movie-server/` — serwer Python (stdlib); `tools/` — narzędzia pomocnicze (np. BiDi).

## Blok metadanych

```js
// ==UserScript==
// @name         Nazwa skryptu
// @namespace    http://tampermonkey.net/
// @version      1.0.0
// @description  Krótki opis co skrypt robi
// @match        https://example.com/*
// @grant        none
// ==/UserScript==
```

- `@match` maksymalnie wąski (konkretna domena/ścieżka), nie `*://*/*`.
- `@grant` tylko te uprawnienia, które skrypt faktycznie wywołuje; inaczej `none`.
- Podbijaj `@version` przy każdej zmianie funkcjonalnej.
- Do auto-update: `@updateURL`/`@downloadURL` wskazujące na raw plik w repo.

## Styl kodu

- IIFE + `'use strict'`, żeby nie zaśmiecać globalnego scope strony.
- Bez bundlerów/zależności — skrypt ma działać jako pojedynczy plik. Biblioteka
  tylko przez `@require` z konkretną, zapiętą wersją.

## Budowanie i testowanie

- Userscripty: po zmianie w `.user.js` najpierw skill `testuj-userscript-bidi`,
  potem w razie potrzeby `zainstaluj-w-tampermonkey`.
- `movie-server`: lokalnie `python3 server.py 9000` (stdlib only; bez pip).

## Dokumentowanie decyzji i ustaleń

- **Zamierzone zachowanie systemu** (kontrakty, progi, capability — co kod SHALL
  robić): jeśli projekt używa OpenSpec, to `openspec/specs/` jest źródłem
  prawdy. Każda zmiana zachowania przechodzi przez `openspec/changes/` i musi
  zostać zmergowana do `specs/` — bez tego kroku spec i kod cicho się
  rozjeżdżają.
- **Efemeryczne ustalenia o zewnętrznych/niekontrolowanych systemach**
  (np. "sprawdzone curlem 2026-09-08, że API zwraca pole X") — zapisuj jako
  komentarz/docstring **przy kodzie**, którego dotyczą, z datą weryfikacji.
  Taki fakt nie opisuje naszego zamierzonego zachowania, więc nie pasuje do
  OpenSpec; osobny plik `.md` obok kodu też się z nim w ciszy rozjedzie,
  a komentarz przy zmienianej linii rzuca się w oczy przy kolejnej edycji.
- Wyjątek: przebieg badań, którego nie da się odtworzyć z kodu ani z historii
  git (co próbowano i dlaczego nie zadziałało) — to trafia do `docs/`.

## Konwencje commitów

- Każda zmiana: commit z opisową wiadomością.
- Nie dodawaj stopki `Co-Authored-By` ani innej atrybucji do commitów.

## movie-server — docelowy hosting (router z home-energy-hub)

- Router OpenWrt, host `japa55.japa` (szczegóły dostępu i wdrożenia:
  `home-energy-hub/AGENTS.md`).
- Python **3.7**, `/usr/bin/python3 → /mnt/sd/usr/bin/python3.7`
  (`home-energy-hub/python_install.sh`).
- Pakiety tylko przez `opkg`, i to w wąskim zestawie: `python3-base`,
  `python3-light`, `python3-logging`, `python3-asyncio`, `python3-urllib`,
  `python3-email`. Brak `pip`/bibliotek zewnętrznych w standardzie (pip bywa
  użyty punktowo dla pojedynczego pakietu, nie jako reguła) — kod musi trzymać
  się stdlib (`urllib`, `http.server`, `json`, `re`).
- Zajęte porty na routerze (sprawdzone `netstat -tlnp` przez SSH, 2026-09-15):
  `22, 53, 80, 111, 443, 502, 6144, 8080, 8090`.
- **movie-server ma nasłuchiwać na porcie 9000** na tym routerze (wolny w
  powyższej liście).
- Sprawdzone realnym uruchomieniem 2026-09-15 (lokalnie, na desktopie pod
  Pythonem 3.14): serwer w `movie-server/` (stdlib only) działa poprawnie.
- **Wdrożone na routerze 2026-09-15**, sprawdzone realnym uruchomieniem:
  - Pliki w `/mnt/sd/movie-server/` (kopiowane przez SSH, wzorcem z
    `home-energy-hub/AGENTS.md`: `cat plik | ssh japa55.japa "cat > ścieżka"`).
  - Keepalive: cron co 1 min → `/mnt/sd/movie-server/run_skrypt.sh server.py 9000`
    (pidfile `/tmp/server.py.pid`). **Nie** restartuj całego routera przy wdrożeniu.
  - Wdrożenie / restart procesu: skill `wdroz-movie-server` (kill tylko z pidfile,
    potem `run_skrypt.sh` — bez `ps | grep` i bez ręcznego drugiego `python3 &`).
  - Działa pod Python 3.7.13, potwierdzone `wget -qO- http://127.0.0.1:9000/trending`
    i `/` bezpośrednio na routerze.
  - Dostępny w LAN pod `http://192.168.55.1:9000/` (adres `br-lan` routera).
  - Planowy reboot routera: niedziela 6:00 `clean_reboot.sh` (osobna sprawa).
