---
name: zainstaluj-w-tampermonkey
description: Zainstaluj lub zaktualizuj plik .user.js w Tampermonkey na komputerze użytkownika (Firefox desktop). Użyj po każdej zmianie w pliku userscriptu, gdy trzeba, żeby użytkownik faktycznie miał nową wersję działającą w przeglądarce.
---

# Instalacja/aktualizacja userscriptu w Tampermonkey

Nie da się tego zrobić w 100% automatycznie — Tampermonkey celowo wymaga
kliknięcia "Zainstaluj"/"Przeinstaluj" w oknie z podglądem kodu, zanim skrypt
zacznie się wykonywać na stronach użytkownika. Próby ominięcia tego (przez
BiDi/Marionette `script.evaluate`, chrome-context, edycję IndexedDB) trafiają
na twarde zabezpieczenia Firefoksa — nie próbuj tego obchodzić.

To, co da się zautomatyzować: przygotowanie i podanie właściwego adresu, tak
żeby zostało tylko jedno kliknięcie użytkownika.

## Krok 1: podbij `@version` w pliku

Tampermonkey pokazuje "Ponowna instalacja"/diff tylko gdy wersja się różni.
Zawsze podbij `@version` przy każdej zmianie funkcjonalnej — inaczej okno
instalacji może pokazać starą treść z cache.

## Krok 2: serwuj plik lokalnie pod `.user.js`

Tampermonkey przechwytuje nawigację na podstawie **rozszerzenia URL**
(`.user.js`) — nie samego `Content-Type`. Serwowanie pliku pod adresem
kończącym się na zwykłe `.js` (np. `/skrypt.js`) **nie zostanie przechwycone**
i Firefox pokaże zwykły podgląd kodu jako tekst.

```python
python -c "
import http.server, socketserver
PORT = 8766
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=r'D:\github\skryptyjs', **kwargs)
    def guess_type(self, path):
        if path.endswith('.user.js') or path.endswith('.js'):
            return 'text/javascript; charset=utf-8'
        return super().guess_type(path)
with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
    httpd.serve_forever()
" &
```

## Pułapka: brak `charset=utf-8` psuje znaki spoza ASCII

`http.server.SimpleHTTPRequestHandler` domyślnie zwraca
`Content-Type: text/javascript` **bez** `charset=utf-8`. Firefox wtedy zgaduje
kodowanie i potrafi błędnie zdekodować znaki spoza ASCII (np. `−` U+2212 MINUS
SIGN zamienia się w widoczny "krzaczek" typu `â^'` w UI skryptu na telefonie).
Zawsze nadpisuj `guess_type()` tak jak wyżej, żeby wymusić `charset=utf-8` —
albo, jeszcze prościej i trwalej: **unikaj w kodzie znaków spoza ASCII**
w stringach trafiających do DOM (np. zwykły `-` zamiast `−`), żeby problem
nie zależał od tego, jak plik zostanie kiedyś zserwowany/przesłany.

## Krok 3: otwórz URL w Firefoksie (ten sam profil co docelowy Tampermonkey)

```
"C:/Program Files/Mozilla Firefox/firefox.exe" "http://127.0.0.1:8766/panscan-zoom-video.user.js"
```

Jeśli Firefox już działa, to polecenie otwiera nową kartę w tym samym oknie —
nie trzeba go zamykać. Poinformuj użytkownika, że ma kliknąć
"Zainstaluj"/"Przeinstaluj"/"Aktualizuj" w oknie Tampermonkeya, które się
pojawi.

## Krok 4: po potwierdzeniu instalacji przez użytkownika

Zweryfikuj działanie skillem `testuj-userscript-bidi`, zamiast zakładać, że
zmiana zadziałała tylko dlatego, że instalacja się powiodła.

## Pułapka: różne profile Firefoksa

Ten sam komputer może mieć kilka profili Firefoksa (`profiles.ini`), a
Tampermonkey może być zainstalowany tylko w jednym z nich. Jeśli użytkownik
mówi "nie widzę Tampermonkeya", sprawdź `extensions.json` w profilu, na
którym faktycznie testujesz:

```
python3 -c "
import json
path = r'C:\Users\<user>\AppData\Roaming\Mozilla\Firefox\Profiles\<profil>\extensions.json'
data = json.load(open(path, encoding='utf-8', errors='replace'))
for a in data.get('addons', []):
    if 'tampermonkey' in a.get('id','').lower():
        print(a.get('id'), a.get('version'), a.get('active'))
"
```

`profiles.ini` może mieć sprzeczne sekcje (`[ProfileN] Default=1` vs
`[Install...] Default=Profiles/...`) — ta druga (`[Install...]`) zwykle
wygrywa w nowszych wersjach Firefoksa i decyduje, który profil otwiera się
domyślnie. Jeśli nie masz pewności, otwórz Firefoksa jawnie z `-P <profil>`.
