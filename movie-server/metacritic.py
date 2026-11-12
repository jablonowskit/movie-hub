"""Metacritic User Score (nie Metascore krytyków).

Źródło: publiczne API backend.metacritic.com używane przez stronę
metacritic.com. Klucz apiKey wyciągany ze strony HTML (jak tmdb_key).

Sprawdzone realnym wywołaniem 2026-10-18:
  - search: /finder/metacritic/search/<q>/web → slug + premiereYear
  - szczegóły: /composer/metacritic/pages/movies/<slug>/web
  - User Score = komponent MetaScoreSummary z max=10 (np. Tenzing → 6.3)
  - Metascore krytyków = MetaScoreSummary z max=100 (celowo pomijamy)
"""
import json
import re
import time
import urllib.parse
import urllib.request

CACHE_TTL_SECONDS = 30 * 60
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
BACKEND = "https://backend.metacritic.com"
# Fallback na wypadek, gdy ekstrakcja ze strony padnie — klucz z HTML
# metacritic.com, sprawdzony 2026-10-18.
_FALLBACK_API_KEY = "1MOZgmNFxvmljaQR1X9KAij9Mo4xAY3u"

_cached_key = None
_cached_key_at = 0.0
_score_cache = {}  # (title_norm, year) -> (ts, result)


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _fetch_json(url):
    return json.loads(_fetch(url))


def _get_api_key():
    global _cached_key, _cached_key_at
    now = time.time()
    if _cached_key and now - _cached_key_at < CACHE_TTL_SECONDS:
        return _cached_key
    try:
        html = _fetch("https://www.metacritic.com/")
        m = re.search(r"apiKey=([A-Za-z0-9_-]{20,})", html)
        if not m:
            m = re.search(r'"apiKey"\s*:\s*"([A-Za-z0-9_-]{20,})"', html)
        if m:
            _cached_key = m.group(1)
            _cached_key_at = now
            return _cached_key
    except Exception:
        pass
    if _cached_key:
        return _cached_key
    return _FALLBACK_API_KEY


def _norm_title(title):
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def _search_movie(title, year=None):
    key = _get_api_key()
    q = urllib.parse.quote(title)
    url = (
        BACKEND + "/finder/metacritic/search/" + q + "/web"
        "?apiKey=" + key +
        "&offset=0&limit=20&format=json&componentType=SearchFilterResults"
    )
    data = _fetch_json(url)
    items = ((data.get("data") or {}).get("items")) or []
    movies = [it for it in items if it.get("type") == "movie"]
    if not movies:
        return None

    want = _norm_title(title)
    year_i = int(year) if year else None

    def score(it):
        s = 0
        if _norm_title(it.get("title")) == want:
            s += 10
        elif want and want in _norm_title(it.get("title")):
            s += 5
        py = it.get("premiereYear")
        if year_i and py == year_i:
            s += 20
        elif year_i and py and abs(py - year_i) <= 1:
            s += 10
        return s

    movies.sort(key=score, reverse=True)
    best = movies[0]
    if score(best) < 5:
        return None
    return best


def _user_score_for_slug(slug):
    key = _get_api_key()
    url = (
        BACKEND + "/composer/metacritic/pages/movies/" +
        urllib.parse.quote(slug) + "/web?apiKey=" + key
    )
    data = _fetch_json(url)
    for c in data.get("components") or []:
        meta = c.get("meta") or {}
        if meta.get("componentType") != "MetaScoreSummary":
            continue
        item = (c.get("data") or {}).get("item") or {}
        # max=10 → User Score; max=100 → Metascore krytyków
        if item.get("max") == 10 and item.get("score") is not None:
            return {
                "score": item["score"],
                "review_count": item.get("reviewCount"),
                "sentiment": item.get("sentiment"),
                "url": "https://www.metacritic.com/movie/" + slug + "/",
            }
    return None


def movie_user_score(title, year=None):
    """Zwraca dict z User Score albo None, gdy brak.

    Przykład (Tenzing, 2026): {"score": 6.3, "review_count": 4, ...}
    """
    if not title:
        return None
    cache_key = (_norm_title(title), str(year or ""))
    now = time.time()
    cached = _score_cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    result = None
    try:
        hit = _search_movie(title, year)
        if hit and hit.get("slug"):
            result = _user_score_for_slug(hit["slug"])
            if result is not None:
                result["title"] = hit.get("title")
                result["slug"] = hit.get("slug")
                result["year"] = hit.get("premiereYear")
    except Exception:
        # Błąd sieci/API — bez cache, inaczej brak MC trzyma się 30 min.
        return None

    if len(_score_cache) > 2000:
        _score_cache.clear()
    _score_cache[cache_key] = (now, result)
    return result
