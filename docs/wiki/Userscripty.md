# Userscripty

## panscan-zoom-video.user.js

Panscan i zoom wideo, pasy letterbox oraz przełączanie playerów. Opis i wersja są w bloku `@description` i `@version` w pliku.

### Instalacja

1. Zainstaluj Tampermonkey (Firefox desktop lub Firefox Android).
2. Otwórz `http://<adres-routera>:9000/panscan-zoom-video.user.js` z sieci LAN routera albo plik z repo.
3. Tampermonkey pokaże okno instalacji. Zatwierdź je.

Aktualizacje idą przez `@updateURL` i `@downloadURL`, które wskazują na adres routera.

## Zasady dla nowych skryptów

- Jeden skrypt to jeden plik `.user.js` w katalogu głównym repo.
- `@match` jak najwęższy (konkretna domena i ścieżka).
- `@grant none`, o ile skrypt nie używa uprawnień Tampermonkey.
- Przy każdej zmianie funkcjonalnej podbijaj `@version`.
