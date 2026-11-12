"""Wyciąga aktualny klucz TMDB API z dwóch niezależnych źródeł trzecich, które
same wołają TMDB wprost z kluczem wpisanym na sztywno w swoim kodzie JS:

- flixmomo.st (Next.js, klucz w /_next/static/chunks/*.js jako
  "https://api.themoviedb.org/3/...?api_key=<klucz>")
- flixmomo.us (bundle Vite/ESM, klucz w zmiennej przekazywanej do
  URLSearchParams({api_key: ...}))

Sprawdzone realnym zapytaniem 2026-09-15: oba źródła zwracają RÓŻNE, ważne
klucze — czyli to naprawdę niezależne źródła, nie kopie tej samej strony.
Dwa źródła zamiast jednego dają odporność na to, że jedno z nich zmieni
strukturę albo zniknie.
"""
import re
import time
import urllib.request

CACHE_TTL_SECONDS = 30 * 60  # na wypadek rotacji klucza po stronie źródłowej
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

_cached_key = None
_cached_at = 0.0


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _find_key_flixmomo_st():
    from urllib.parse import urljoin

    home = "https://flixmomo.st/"
    html = _fetch(home)
    chunk_paths = sorted(set(re.findall(r'src="(/_next/static/chunks/[a-zA-Z0-9_.-]+\.js)"', html)))
    for path in chunk_paths:
        js = _fetch(urljoin(home, path))
        m = re.search(r"api\.themoviedb\.org/3/[a-zA-Z0-9/_-]+\?api_key=([a-f0-9]{32})", js)
        if m:
            return m.group(1)
    raise RuntimeError("Nie znaleziono klucza w JS chunkach flixmomo.st")


def _find_key_flixmomo_us():
    home = "https://flixmomo.us/"
    html = _fetch(home)
    bundle_paths = sorted(set(re.findall(r'src="(/js/[a-zA-Z0-9_.-]+\.js)"', html)))
    for path in bundle_paths:
        js = _fetch("https://flixmomo.us" + path)
        m = re.search(r"api_key:([a-zA-Z_$][a-zA-Z0-9_$]*)", js)
        if not m:
            continue
        var_name = re.escape(m.group(1))
        m2 = re.search(var_name + r'="([a-f0-9]{32})"', js)
        if m2:
            return m2.group(1)
    raise RuntimeError("Nie znaleziono klucza w bundle'u flixmomo.us")


SOURCES = [
    ("flixmomo.st", _find_key_flixmomo_st),
    ("flixmomo.us", _find_key_flixmomo_us),
]


def _find_api_key():
    errors = []
    for name, finder in SOURCES:
        try:
            return finder()
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise RuntimeError("Wszystkie źródła klucza TMDB zawiodły: " + "; ".join(errors))


def get_api_key():
    global _cached_key, _cached_at
    now = time.time()
    if _cached_key and now - _cached_at < CACHE_TTL_SECONDS:
        return _cached_key
    try:
        _cached_key = _find_api_key()
        _cached_at = now
    except Exception as e:
        if _cached_key:
            # Wszystkie źródła padły, ale stary klucz może wciąż działać
            # (TMDB rzadko unieważnia klucze natychmiast) — lepiej spróbować
            # niż od razu wywalić błąd całej strony.
            return _cached_key
        raise RuntimeError(
            "Nie udało się pobrać klucza TMDB API z żadnego źródła i brak "
            "zapasowego z poprzedniego udanego pobrania: " + str(e)
        )
    return _cached_key
