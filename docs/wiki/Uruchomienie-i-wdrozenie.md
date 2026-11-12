# Uruchomienie i wdrożenie

## Lokalnie

```bash
cd movie-server
python server.py 9000
# → http://localhost:9000/
```

Wymagany jest Python 3.7 lub nowszy. Kod używa tylko biblioteki standardowej, więc nie trzeba instalować pakietów.

## Router OpenWrt

- Host SSH: `<router>`
- Katalog: `<katalog-na-routerze>`
- Port: `9000`
- Adres w LAN: `http://<adres-routera>:9000/`
Wdrożenie zmian:

1. Skopiuj zmienione pliki na router przez SSH.
2. Zmiany w `*.py` wymagają restartu procesu serwera.
3. Zmiany w `static/index.html` działają po odświeżeniu strony (Ctrl+F5), bez restartu.

Wdrażaj tylko serwer, nie restartuj całego routera.

## Weryfikacja

```bash
wget -qO- http://localhost:9000/trending | head -c 200
wget -qO- "http://localhost:9000/trending/movie?page=2" | head -c 200
```
