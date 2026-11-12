#!/bin/sh
set -eu

[ -f /root/.profile ] && . /root/.profile

export PYTHONUNBUFFERED=1

# jesli brak python3 to koniec
[ -x /usr/bin/python3 ] || exit 0

# Nie wskrzeszaj uslug podczas planowego restartu (clean_reboot.sh trzyma lock)
[ -f /tmp/reboot_in_progress ] && exit 0

# pierwszy argument - program do uruchomienia (domyslnie server.py)
PROGRAM="${1:-server.py}"
if [ "$#" -gt 0 ]; then
    shift
fi

# Znormalizuj do sciezki absolutnej (tak widac proces w cmdline)
case "$PROGRAM" in
    /*) PROGRAM_PATH="$PROGRAM" ;;
    *)  PROGRAM_PATH="/mnt/sd/movie-server/$PROGRAM" ;;
esac

# prosta rotacja logow (BusyBox-friendly, bez logrotate)
LOG_MAX_DAYS="${LOG_MAX_DAYS:-7}"
LOG_MAX_FILES="${LOG_MAX_FILES:-8}"
PROG_BASENAME=$(basename "$PROGRAM")
LOG_GLOB="/tmp/${PROG_BASENAME}_*.log"

find /tmp -maxdepth 1 -type f -name "${PROG_BASENAME}_*.log" -mtime +"$LOG_MAX_DAYS" -delete 2>/dev/null || true

COUNT="$(ls -1 $LOG_GLOB 2>/dev/null | wc -l | tr -d ' ')"
if [ "${COUNT:-0}" -gt "$LOG_MAX_FILES" ]; then
    REMOVE_COUNT=$((COUNT - LOG_MAX_FILES))
    ls -1t $LOG_GLOB 2>/dev/null | tail -n "$REMOVE_COUNT" | while read -r old_log; do
        [ -n "${old_log:-}" ] && rm -f "$old_log"
    done
fi

# nie uruchamiaj duplikatu:
# 1) pidfile (bez pgrep)
# 2) fallback po cmdline
PIDFILE="/tmp/${PROG_BASENAME}.pid"
if [ -f "$PIDFILE" ]; then
    OLD_PID="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [ -n "${OLD_PID:-}" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        exit 0
    fi
    # Proces byl sledzony, ale nie zyje => padl. Zapisz trwale zdarzenie na SD z ogonem
    # logu (przyczyna). Tylko przy ZMIANIE ogona - inaczej petla restartow spamowalaby.
    EVENTS="/mnt/sd/movie-server/events.log"
    LASTLOG="$(ls -1t $LOG_GLOB 2>/dev/null | head -1)"
    if [ -n "${LASTLOG:-}" ]; then
        NEWHASH="$(tail -n 15 "$LASTLOG" 2>/dev/null | md5sum | awk '{print $1}')"
        HASHFILE="/tmp/.${PROG_BASENAME}.lastevent"
        if [ "$NEWHASH" != "$(cat "$HASHFILE" 2>/dev/null || true)" ]; then
            {
                echo "==== $(date '+%F %T') ${PROG_BASENAME} nie zyje (pid ${OLD_PID:-?}) - ogon logu ===="
                tail -n 15 "$LASTLOG" 2>/dev/null
                echo ""
            } >> "$EVENTS" 2>/dev/null || true
            echo "$NEWHASH" > "$HASHFILE" 2>/dev/null || true
            # ogranicz plik zdarzen do ostatnich ~400 linii
            tail -n 400 "$EVENTS" > "${EVENTS}.tmp" 2>/dev/null && mv -f "${EVENTS}.tmp" "$EVENTS" 2>/dev/null || true
        fi
    fi
    rm -f "$PIDFILE" 2>/dev/null || true
fi

if [ "$#" -gt 0 ]; then
    ps w | grep -F " -u $PROGRAM_PATH $*" | grep -v grep >/dev/null 2>&1 && exit 0
else
    ps w | grep -F " -u $PROGRAM_PATH" | grep -v grep >/dev/null 2>&1 && exit 0
fi

# przejdz do katalogu roboczego
cd /mnt/sd/movie-server/ || {
    echo "Blad: nie mozna przejsc do /mnt/sd/movie-server/" >&2
    exit 1
}

# Dodaj date do nazwy pliku logu
DATE=$(date +%Y%m%d)
echo "$$" > "$PIDFILE"
exec python3 -u "$PROGRAM_PATH" "$@" >> /tmp/${PROG_BASENAME}_${DATE}.log 2>&1
