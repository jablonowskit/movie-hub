import json
import urllib.request
from urllib.parse import urlencode

from tmdb_key import get_api_key

BASE_URL = "https://api.themoviedb.org/3"


def _get(path, params=None):
    params = dict(params or {})
    params["api_key"] = get_api_key()
    url = BASE_URL + path + "?" + urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def trending_movies(page=1):
    return _get("/trending/movie/day", {"page": page})


def trending_tv(page=1):
    return _get("/trending/tv/day", {"page": page})


def search(query):
    return _get("/search/multi", {"query": query})


# Kategorie "What's Popular": Streaming / W TV / For Rent / W Kinach.
# Sprawdzone realnie 2026-09-15 przeciw TMDB API:
#  - streaming -> discover/movie z with_watch_monetization_types=flatrate
#  - w_tv      -> tv/on_the_air (seriale aktualnie emitowane)
#  - for_rent  -> discover/movie z with_watch_monetization_types=rent
#  - w_kinach  -> movie/now_playing
WATCH_REGION = "PL"


def popular_streaming(page=1):
    return _get("/discover/movie", {
        "with_watch_monetization_types": "flatrate",
        "watch_region": WATCH_REGION,
        "sort_by": "popularity.desc",
        "page": page,
    })


def popular_tv(page=1):
    return _get("/tv/on_the_air", {"page": page})


def popular_for_rent(page=1):
    return _get("/discover/movie", {
        "with_watch_monetization_types": "rent",
        "watch_region": WATCH_REGION,
        "sort_by": "popularity.desc",
        "page": page,
    })


def popular_in_cinemas(page=1):
    return _get("/movie/now_playing", {"region": WATCH_REGION, "page": page})


def movie_details(movie_id):
    # language=pl-PL: overview po polsku (sprawdzone 2026-10-18).
    return _get("/movie/" + str(movie_id), {"language": "pl-PL"})


def tv_details(tv_id):
    # language=pl-PL: overview po polsku (sprawdzone 2026-10-18).
    return _get("/tv/" + str(tv_id), {"language": "pl-PL"})


def season_details(tv_id, season_number):
    return _get("/tv/" + str(tv_id) + "/season/" + str(season_number), {"language": "pl-PL"})


def movie_quality(movie_id):
    """Określa jakość filmu (HD vs CAM) na podstawie typów wydań w TMDB:
    Typ 4 (Digital/VOD) lub 5 (Physical/Blu-ray) już wydane -> 'HD'
    Typ 1, 2, 3 (tylko kino) już wydane, bez digital/physical -> 'CAM'
    Brak jakiegokolwiek wydania z datą <= dziś (przed premierą) -> 'CAM'
    (checkbox „Ukryj CAM” ma też chować filmy przed premierą.)
    """
    import datetime
    today = datetime.date.today().isoformat()
    try:
        data = _get("/movie/" + str(movie_id) + "/release_dates")
        results = data.get("results", [])
        has_past_release = False
        has_theatrical = False
        for c in results:
            for d in c.get("release_dates", []):
                t = d.get("type")
                dt = (d.get("release_date") or "")[:10]
                if dt and dt <= today:
                    has_past_release = True
                    if t in (4, 5):
                        return "HD"
                    elif t in (1, 2, 3):
                        has_theatrical = True
        # Przed premierą albo tylko kino — traktuj jak CAM (do ukrycia checkboxem).
        if has_theatrical or not has_past_release:
            return "CAM"
        return None
    except Exception:
        return None

