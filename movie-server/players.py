"""Lista playerów — sync z getPlayers() w panscan-zoom-video.user.js.

Kolejność (2026-10-28, Verity TMDB 1283515): malejący max BANDWIDTH z HLS/DASH
— docs/2026-10-28-flixmomo-player-quality.md (nie sama rozdzielczość).
Na końcu VidSrc (vidsrc.to): słabsza jakość, ale duże pokrycie katalogu.
URL TV: wzorce jak flixmomo / HTTP 200 na embedach (sprawdzone 2026-10-28).
"""


def get_players(media_type, media_id, season=None, episode=None):
    if media_type == "movie":
        return [
            {"name": "VidSrc.su", "url": f"https://vidsrc.su/movie/{media_id}"},
            {"name": "Filmu", "url": f"https://embed.filmu.in/movie/{media_id}"},
            {"name": "VixSrc", "url": f"https://vixsrc.to/movie/{media_id}"},
            {"name": "CineSrc", "url": f"https://cinesrc.st/embed/movie/{media_id}"},
            {"name": "Cinezo", "url": f"https://player.cinezo.live/embed/movie/{media_id}"},
            {"name": "MoviesAPI", "url": f"https://moviesapi.to/movie/{media_id}"},
            {"name": "VidSrc", "url": f"https://vidsrc.to/embed/movie/{media_id}"},
        ]

    s = season or "1"
    e = episode or "1"
    return [
        {"name": "VidSrc.su", "url": f"https://vidsrc.su/tv/{media_id}/{s}/{e}"},
        {"name": "Filmu", "url": f"https://embed.filmu.in/tv/{media_id}/{s}/{e}"},
        {"name": "VixSrc", "url": f"https://vixsrc.to/tv/{media_id}/{s}/{e}"},
        {"name": "CineSrc", "url": f"https://cinesrc.st/embed/tv/{media_id}?s={s}&e={e}"},
        {"name": "Cinezo", "url": f"https://player.cinezo.live/embed/tv/{media_id}/{s}/{e}"},
        {"name": "MoviesAPI", "url": f"https://moviesapi.to/tv/{media_id}/{s}/{e}"},
        {"name": "VidSrc", "url": f"https://vidsrc.to/embed/tv/{media_id}/{s}/{e}"},
    ]
