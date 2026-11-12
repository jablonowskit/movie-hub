"""Serwer wyszukiwania filmów/seriali (TMDB) i generowania linków do playerów.

Endpointy:
  GET /                                      -> strona dla użytkownika (static/index.html)
  GET /panscan-zoom-video.user.js            -> userscript (Tampermonkey @updateURL/@downloadURL)
  GET /search?q=...                         -> wyniki wyszukiwania TMDB (JSON)
  GET /trending                              -> trending movie+tv na dziś (JSON)
  GET /trending/<movie|tv>?page=N            -> kolejna strona trending (JSON, TMDB)
  GET /popular/<kategoria>?page=N            -> kolejna strona kategorii "What's Popular" (JSON)
  GET /movie/<id>                            -> szczegóły filmu, w tym overview (JSON, pl-PL)
  GET /movie/<id>/metacritic                 -> Metacritic User Score (JSON; nie Metascore)
  GET /tv/<id>                               -> szczegóły serialu, w tym lista sezonów (JSON)
  GET /tv/<id>/season/<season>               -> szczegóły sezonu, w tym daty premiery odcinków (JSON)
  GET /players/movie/<id>                    -> lista playerów dla filmu (JSON)
  GET /players/tv/<id>/<season>/<episode>    -> lista playerów dla odcinka (JSON)
  GET /watch/movie/<id>                      -> redirect 302 do pierwszego playera
  GET /watch/tv/<id>/<season>/<episode>      -> redirect 302 do pierwszego playera

Uruchomienie: python server.py [port]  (domyślnie 9000)
"""
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from tmdb import (
    search, trending_movies, trending_tv,
    popular_streaming, popular_tv, popular_for_rent, popular_in_cinemas,
    movie_details, tv_details, season_details, movie_quality,
)
from players import get_players
from player_info import players_extra
from metacritic import movie_user_score

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(ROOT_DIR, "static")
# Userscript: na routerze leży w ROOT_DIR; lokalnie bywa w katalogu nad movie-server/.
_USERSCRIPT_CANDIDATES = (
    os.path.join(ROOT_DIR, "panscan-zoom-video.user.js"),
    os.path.join(ROOT_DIR, "..", "panscan-zoom-video.user.js"),
)

POPULAR_CATEGORIES = {
    "streaming": popular_streaming,
    "w_tv": popular_tv,
    "for_rent": popular_for_rent,
    "w_kinach": popular_in_cinemas,
}

ROUTES = [
    (re.compile(r"^/$"), "index"),
    (re.compile(r"^/search$"), "search"),
    (re.compile(r"^/trending$"), "trending"),
    (re.compile(r"^/trending/(?P<kind>movie|tv)$"), "trending_kind"),
    (re.compile(r"^/movie/(?P<id>\d+)/quality$"), "movie_quality"),
    (re.compile(r"^/movie/(?P<id>\d+)/metacritic$"), "movie_metacritic"),
    (re.compile(r"^/movie/(?P<id>\d+)$"), "movie_details"),
    (re.compile(r"^/tv/(?P<id>\d+)$"), "tv_details"),
    (re.compile(r"^/tv/(?P<id>\d+)/season/(?P<season>\d+)$"), "season_details"),
    (re.compile(r"^/popular/(?P<category>streaming|w_tv|for_rent|w_kinach)$"), "popular"),
    (re.compile(r"^/players/movie/(?P<id>\d+)$"), "players_movie"),
    (re.compile(r"^/players/tv/(?P<id>\d+)/(?P<season>\d+)/(?P<episode>\d+)$"), "players_tv"),
    (re.compile(r"^/watch/movie/(?P<id>\d+)$"), "watch_movie"),
    (re.compile(r"^/watch/tv/(?P<id>\d+)/(?P<season>\d+)/(?P<episode>\d+)$"), "watch_tv"),
    (re.compile(r"^/panscan-zoom-video\.user\.js$"), "userscript"),
]


def _page(query):
    """Numer strony z ?page=N (TMDB: 1..500); zły/brak parametru -> 1."""
    try:
        page = int((query.get("page") or ["1"])[0])
    except ValueError:
        page = 1
    return min(max(page, 1), 500)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_response(self, code, message=None):
        self._responded = True
        super().send_response(code, message)

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, url):
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    def _file(self, path, content_type):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._responded = False
        parsed = urlparse(self.path)
        for pattern, name in ROUTES:
            m = pattern.match(parsed.path)
            if not m:
                continue
            try:
                getattr(self, "handle_" + name)(m.groupdict(), parse_qs(parsed.query))
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                if self._responded:
                    self.log_message("błąd po wysłaniu nagłówków: %s", e)
                else:
                    self._json(502, {"error": str(e)})
            return
        self._json(404, {"error": "not found"})

    def handle_index(self, params, query):
        self._file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")

    def handle_userscript(self, params, query):
        path = None
        for cand in _USERSCRIPT_CANDIDATES:
            if os.path.isfile(cand):
                path = cand
                break
        if not path:
            self._json(404, {"error": "brak panscan-zoom-video.user.js"})
            return
        # text/javascript + charset — TM aktualizuje po @version; URL musi kończyć się .user.js
        self._file(path, "text/javascript; charset=utf-8")

    def handle_search(self, params, query):
        q = (query.get("q") or [""])[0]
        if not q:
            self._json(400, {"error": "brak parametru q"})
            return
        self._json(200, search(q))

    def handle_trending(self, params, query):
        self._json(200, {"movies": trending_movies(), "tv": trending_tv()})

    def handle_trending_kind(self, params, query):
        fetch = trending_movies if params["kind"] == "movie" else trending_tv
        self._json(200, fetch(_page(query)))

    def handle_movie_quality(self, params, query):
        q = movie_quality(params["id"])
        self._json(200, {"quality": q})

    def handle_movie_details(self, params, query):
        self._json(200, movie_details(params["id"]))

    def handle_movie_metacritic(self, params, query):
        # title/year z query (z karty listy) — omija dodatkowe TMDB details.
        title = (query.get("title") or [""])[0].strip() or None
        year = (query.get("year") or [""])[0].strip() or None
        alt_title = (query.get("alt") or [""])[0].strip() or None
        if not title:
            details = movie_details(params["id"])
            title = details.get("original_title") or details.get("title")
            year = (details.get("release_date") or "")[:4] or None
            alt_title = details.get("title")
        score = movie_user_score(title, year)
        if score is None and alt_title and alt_title != title:
            score = movie_user_score(alt_title, year)
        self._json(200, {"metacritic_user": score})

    def handle_tv_details(self, params, query):
        self._json(200, tv_details(params["id"]))

    def handle_season_details(self, params, query):
        self._json(200, season_details(params["id"], params["season"]))

    def handle_popular(self, params, query):
        fetch = POPULAR_CATEGORIES[params["category"]]
        self._json(200, fetch(_page(query)))

    def handle_players_movie(self, params, query):
        mid = params["id"]
        players = get_players("movie", mid)
        payload = players_extra("movie", mid, players=players)
        self._json(200, payload)

    def handle_players_tv(self, params, query):
        mid = params["id"]
        season = params["season"]
        episode = params["episode"]
        players = get_players("tv", mid, season, episode)
        payload = players_extra("tv", mid, season, episode, players=players)
        self._json(200, payload)

    def handle_watch_movie(self, params, query):
        players = get_players("movie", params["id"])
        self._redirect(players[0]["url"])

    def handle_watch_tv(self, params, query):
        players = get_players("tv", params["id"], params["season"], params["episode"])
        self._redirect(players[0]["url"])


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"movie-server nasłuchuje na http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
