---
name: wgraj-userscript-telefon
description: Zainstaluj lub zaktualizuj panscan-zoom-video.user.js w Tampermonkey na telefonie (Firefox Android) przez ADB. Użyj gdy użytkownik mówi „wgraj na telefon”, „aktualizuj skrypt na telefonie” albo po zmianie userscriptu/wdrożeniu na router.
---

# Userscript → Firefox + Tampermonkey na telefonie

Bez roota **nie** da się zapisać skryptu wprost do danych Firefoksa. Działa
otwarcie URL kończącego się na `.user.js` — Tampermonkey przechwytuje i pokazuje
dialog instalacji/aktualizacji (jedno kliknięcie).

## Wymagania

- `adb devices` → stan `device` (skill `polacz-telefon`)
- Telefon w LAN routera (Wi‑Fi)
- Na routerze musi być świeży plik:
  `http://192.168.55.1:9000/panscan-zoom-video.user.js`
  (wdrożenie: skill `wdroz-movie-server`, plik + restart gdy zmienił się `server.py`)
- Pakiet: `org.mozilla.firefox`

## Preferowana ścieżka (LAN / router)

```powershell
adb shell input keyevent 224
adb shell input swipe 540 1800 540 500 200
adb shell am force-stop org.mozilla.firefox
adb shell am start -a android.intent.action.VIEW -d "http://192.168.55.1:9000/panscan-zoom-video.user.js" -p org.mozilla.firefox
```

Potem zrzut ekranu (`steruj-telefonem`) i tap w **Aktualizuj** / **Overwrite** /
**Przeinstaluj**. UI dump WebView często **nie** ma tekstu przycisku — celuj
wizualnie (środek ekranu nad „Anuluj”) albo poproś użytkownika o klik.

## Awaryjna ścieżka (PC :8766 + adb reverse)

Gdy router niedostępny z telefonu:

1. Serwuj repo na `127.0.0.1:8766` (jak w `zainstaluj-w-tampermonkey`, UTF-8).
2. `adb reverse tcp:8766 tcp:8766`
3. Otwórz `http://127.0.0.1:8766/panscan-zoom-video.user.js` w Firefoxie.

## Metadane skryptu

W `panscan-zoom-video.user.js` muszą być (LAN):

```
// @updateURL    http://192.168.55.1:9000/panscan-zoom-video.user.js
// @downloadURL  http://192.168.55.1:9000/panscan-zoom-video.user.js
```

Przy każdej zmianie funkcjonalnej **podbij `@version`** — inaczej TM nie pokaże
aktualizacji. Pierwsza instalacja z URL routera ustawia updateURL; wcześniej
zainstalowane z `127.0.0.1:8766` dostaną ostrzeżenie o zmianie adresu — normalne,
klika się **Aktualizuj**.

## Czego nie robić

- Zakładać, że `adb push` do `/sdcard/Download/` = instalacja w Tampermonkey
  (to tylko kopia pliku; instalacja = dialog TM).
- Czytać listy skryptów TM z `/data/data/org.mozilla.firefox` bez roota
  (`polacz-telefon`).
