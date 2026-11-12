"""Dodatkowe info przy playerach — sprawdzone realnymi wywołaniami 2026-10-18
(CineSrc TV season/episode: 2026-10-28):

- CineSrc napisy PL: POST https://cinesrc.st/api/subtitles/search
  film: {"tmdbId": <int>}; TV: {"tmdbId", "season", "episode"}
  (sam tmdbId dla serialu → 0 wyników; z s/e np. X-Files 4087/1/1 → pl:11).
  OpenSubtitles; language pl/pol lub display \"Polish\".
- Cinezo napisy PL: GET https://proxy1.flikhub.net/subtitles/movie/{id}
  (TV: /subtitles/tv/{id}/{s}/{e}); wymaga Origin/Referer player.cinezo.live;
  pola label (np. \"Polish\") → VTT na cache.vdrk.site (nie OpenSubtitles).
- VidZee języki: GET https://core.vidzee.wtf/streams/languages/movie/{id}
  (TV: /streams/languages/tv/{id}/{s}/{e}) → {\"languages\":[\"English\",…]};
  liczymy wpisy Polish/pl (to lista języków audio/napisów z backendu, nie
  OpenSubtitles). Jakości (1080p) API nie ma.

VidSrc /info (1080p) celowo pomijamy — etykieta rozdzielczości nie oddaje
jakości przy mocnej kompresji.

Dostępność embedu (GET, 2026-10-28, X-Files tv/4087/1/1): FlaxMovies → HTTP 404;
VidZee player.vidzee.wtf → TimeoutError z urllib (w przeglądarce bywa OK) —
dlatego timeout/sieć = unknown (None), nie „niedostępny”. Niedostępny tylko
przy HTTP ≥400. Hosty VidZee pomijamy w probe (zawsze timeout, ~4s strata).
"""
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

CACHE_TTL = 30 * 60
# VidZee core.vidzee.wtf często wisi do timeoutu (sprawdzone 2026-10-28: 15s
# TimeoutError na /streams/languages/tv/4087/1/1) — krótki limit, żeby nie
# blokował równoległego players_extra.
_TIMEOUT = 8
_VIDZEE_TIMEOUT = 3
_EMBED_TIMEOUT = 4
# Serwerowy GET na te hosty zawsze timeoutuje (2026-10-28) — nie oznaczaj
# „niedostępny” i nie czekaj.
_AVAIL_SKIP_HOSTS = frozenset({
    "player.vidzee.wtf",
    "core.vidzee.wtf",
})
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36"
_cache = {}


_CACHE_MAX = 2000


def _prune(now):
    if len(_cache) <= _CACHE_MAX:
        return
    for k in [k for k, (ts, _) in _cache.items() if now - ts >= CACHE_TTL]:
        del _cache[k]
    if len(_cache) > _CACHE_MAX:
        _cache.clear()


def _cached(key, fetcher, cache_zero=True):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    try:
        val = fetcher()
    except Exception:
        # Błędu sieci nie cache'ujemy — inaczej chwilowy fail zostaje na TTL.
        return None
    if val is None:
        # None = timeout/nie wiadomo (probe_embed_available) — też bez cache.
        return None
    # Puste 0 bywa chwilowym flakiem API (np. CineSrc) — bez cache, żeby
    # nie trzymać fałszywego PL 0 przez cały TTL (sprawdzone 2026-10-28).
    if val == 0 and not cache_zero:
        return 0
    _prune(now)
    _cache[key] = (now, val)
    return val


def _is_polish(label):
    lab = (label or "").strip().lower()
    return lab in ("pl", "pol", "polish") or "polish" in lab


def cinesrc_pl_subs(media_type, media_id, season=None, episode=None):
    """Liczba ścieżek napisów PL z CineSrc (OpenSubtitles), albo None."""
    payload = {"tmdbId": int(media_id)}
    if media_type == "tv" and season is not None and episode is not None:
        payload["season"] = int(season)
        payload["episode"] = int(episode)
        key = ("cpl", "tv", str(media_id), str(season), str(episode))
    else:
        key = ("cpl", "movie", str(media_id))

    def fetch():
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://cinesrc.st/api/subtitles/search",
            data=body,
            headers={
                "User-Agent": _UA,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://cinesrc.st",
                "Referer": "https://cinesrc.st/",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        n = 0
        for s in data.get("subtitles") or []:
            lang = (s.get("language") or "").lower()
            display = s.get("display") or ""
            if lang in ("pl", "pol") or "Polish" in display:
                n += 1
        return n

    return _cached(key, fetch, cache_zero=False)


def cinezo_pl_subs(media_type, media_id, season=None, episode=None):
    """Liczba napisów PL z proxy Cinezo (flikhub), albo None."""
    if media_type == "tv" and season is not None and episode is not None:
        path = "/subtitles/tv/%s/%s/%s" % (media_id, season, episode)
        key = ("zopl", "tv", str(media_id), str(season), str(episode))
        referer = "https://player.cinezo.live/embed/tv/%s/%s/%s" % (
            media_id, season, episode
        )
    else:
        path = "/subtitles/movie/%s" % media_id
        key = ("zopl", "movie", str(media_id))
        referer = "https://player.cinezo.live/embed/movie/%s" % media_id

    def fetch():
        req = urllib.request.Request(
            "https://proxy1.flikhub.net" + path,
            headers={
                "User-Agent": _UA,
                "Accept": "application/json",
                "Origin": "https://player.cinezo.live",
                "Referer": referer,
            },
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, dict):
            items = data.get("subtitles") or data.get("data") or []
        else:
            items = data or []
        n = 0
        for s in items:
            if _is_polish(s.get("label") or s.get("language")):
                n += 1
        return n

    return _cached(key, fetch)


def vidzee_pl_langs(media_type, media_id, season=None, episode=None):
    """Ile wpisów Polish w liście języków VidZee, albo None przy błędzie."""
    if media_type == "tv" and season is not None and episode is not None:
        path = "/streams/languages/tv/%s/%s/%s" % (media_id, season, episode)
        key = ("vzpl", "tv", str(media_id), str(season), str(episode))
    else:
        path = "/streams/languages/movie/%s" % media_id
        key = ("vzpl", "movie", str(media_id))

    def fetch():
        req = urllib.request.Request(
            "https://core.vidzee.wtf" + path,
            headers={"User-Agent": _UA, "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=_VIDZEE_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        n = 0
        for lang in data.get("languages") or []:
            if _is_polish(lang):
                n += 1
        return n

    return _cached(key, fetch)


def probe_embed_available(url):
    """True = OK, False = HTTP≥400 (niedostępny), None = nie wiadomo (timeout)."""
    host = (urlparse(url).hostname or "").lower()
    if host in _AVAIL_SKIP_HOSTS or host.endswith(".vidzee.wtf"):
        return None

    key = ("avail", url)

    def fetch():
        req = urllib.request.Request(
            url,
            headers={"User-Agent": _UA, "Accept": "text/html,*/*"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=_EMBED_TIMEOUT) as resp:
                return int(getattr(resp, "status", 200) or 200) < 400
        except urllib.error.HTTPError as e:
            return False if int(e.code or 500) >= 400 else None
        except Exception:
            # Timeout / DNS — nie cache'ujemy jako False (VidZee fałszywie
            # „niedostępny na wszystkich”, 2026-10-28).
            return None

    return _cached(key, fetch)


def players_extra(media_type, media_id, season=None, episode=None, players=None):
    """Badge'e PL + available — zewnętrzne GET/POST równolegle (ThreadPool)."""
    players = [dict(p) for p in (players or [])]
    names = {p.get("name") for p in players}
    jobs = {}
    if "CineSrc" in names:
        jobs["cinesrc_pl_subs"] = (
            cinesrc_pl_subs, (media_type, media_id, season, episode)
        )
    if "Cinezo" in names:
        jobs["cinezo_pl_subs"] = (
            cinezo_pl_subs, (media_type, media_id, season, episode)
        )
    if "VidZee" in names:
        jobs["vidzee_pl_subs"] = (
            vidzee_pl_langs, (media_type, media_id, season, episode)
        )
    for i, p in enumerate(players):
        jobs[("avail", i)] = (probe_embed_available, (p["url"],))

    out = {
        "cinesrc_pl_subs": None,
        "cinezo_pl_subs": None,
        "vidzee_pl_subs": None,
    }
    avail = {}
    workers = max(3, len(jobs))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(fn, *args): key for key, (fn, args) in jobs.items()
        }
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                val = fut.result()
            except Exception:
                val = None
            if isinstance(key, tuple) and key[0] == "avail":
                avail[key[1]] = val
            else:
                out[key] = val

    for i, p in enumerate(players):
        # False → niedostępny; True/None → bez badge (None = nie sprawdzono)
        if i in avail:
            p["available"] = avail[i]
        else:
            p["available"] = None
    out["players"] = players
    return out
