// ==UserScript==
// @name         Panscan / Zoom video
// @namespace    local
// @version      2.14
// @description  Panscan + auto-pasy + playery (bitrate + VidSrc.to pokrycie)
// @match        *://*/*
// @grant        none
// @run-at       document-start
// @updateURL    http://192.168.55.1:9000/panscan-zoom-video.user.js
// @downloadURL  http://192.168.55.1:9000/panscan-zoom-video.user.js
// ==/UserScript==

(function () {
  'use strict';
  let scale = 1;
  let v = null;
  let playerIdx = 0;
  let cachedCtx = null;

  // @match *://*/* — ps-switch może przyjść od dowolnej ramki (reklamy),
  // więc nawigujemy wyłącznie na https do hostów z getPlayers().
  const PLAYER_HOST_RE = /(^|\.)(vidsrc\.su|filmu\.in|vixsrc\.to|cinesrc\.st|player\.cinezo\.live|moviesapi\.to|vidsrc\.to)$/i;
  function isPlayerUrl(url) {
    try {
      const u = new URL(url);
      return u.protocol === 'https:' && PLAYER_HOST_RE.test(u.hostname);
    } catch (e) { return false; }
  }

  if (window === window.top) {
    window.addEventListener('message', e => {
      const d = e.data;
      if (!d || typeof d !== 'object') return;
      if (d.type === 'ps-switch' && typeof d.url === 'string' && isPlayerUrl(d.url)) location.assign(d.url);
      if (d.type === 'ps-get-context') {
        let ctx = parseUrl(location.href) || parseFromIframes();
        if (ctx && e.source) e.source.postMessage({ type: 'ps-context', ctx: ctx }, '*');
      }
      if (d.type === 'ps-get-href' && e.source) {
        e.source.postMessage({ type: 'ps-href', href: location.href }, '*');
      }
    });
  }

  function findVideo() { return document.querySelector('video'); }

  function applyScale() {
    if (!v || !v.isConnected) v = findVideo();
    if (!v) return;
    v.style.transform = 'scale(' + scale + ')';
    v.style.transformOrigin = 'center center';
    const p = v.parentElement;
    if (p) p.style.overflow = 'hidden';
  }

  let presetIdx = 0;
  const presets = [1, 1.20, 1.34, 1.78]; // brak, ~1.85:1, ~2.39:1, ~4:3 pillar

  function autoZoom() {
    if (v && v.videoWidth) {
      const w = v.videoWidth, h = v.videoHeight;
      const c = document.createElement('canvas');
      c.width = w; c.height = h;
      const ctx = c.getContext('2d');
      try {
        ctx.drawImage(v, 0, 0, w, h);
        const d = ctx.getImageData(0, 0, w, h).data;
        const isDark = i => d[i] + d[i + 1] + d[i + 2] < 60;
        const xs = [w * 0.25 | 0, w * 0.5 | 0, w * 0.75 | 0];
        const ys = [h * 0.25 | 0, h * 0.5 | 0, h * 0.75 | 0];
        const rowDark = y => xs.every(x => isDark((y * w + x) * 4));
        const colDark = x => ys.every(y => isDark((y * w + x) * 4));
        let top = 0; while (top < h / 2 && rowDark(top)) top++;
        let bot = 0; while (bot < h / 2 && rowDark(h - 1 - bot)) bot++;
        let left = 0; while (left < w / 2 && colDark(left)) left++;
        let right = 0; while (right < w / 2 && colDark(w - 1 - right)) right++;
        const vbar = Math.min(top, bot), hbar = Math.min(left, right);
        let s = 1;
        if (vbar > 2) s = Math.max(s, h / (h - 2 * vbar));
        if (hbar > 2) s = Math.max(s, w / (w - 2 * hbar));
        if (s > 1.02) { scale = Math.min(s, 2.5); applyScale(); return; }
      } catch (e) { /* zatruty canvas -> presety */ }
    }
    presetIdx = (presetIdx + 1) % presets.length;
    scale = presets[presetIdx];
    applyScale();
  }

  function makeBtn(txt, onClick) {
    const b = document.createElement('button');
    b.textContent = txt;
    b.style.cssText =
      'width:34px;height:34px;font-size:16px;font-weight:bold;' +
      'background:#1565ff;color:#fff;border:none;border-radius:6px;' +
      'cursor:pointer;opacity:.85;';
    b.onclick = e => { e.stopPropagation(); e.preventDefault(); onClick(); };
    return b;
  }

  function parseUrl(hrefOrPath) {
    let path = hrefOrPath;
    let search = '';
    try {
      const u = hrefOrPath.includes('://')
        ? new URL(hrefOrPath)
        : new URL(hrefOrPath, 'https://x.invalid');
      path = u.pathname;
      search = u.search;
    } catch (e) { /* leave as path */ }
    let m = path.match(/\/(?:embed\/)?movie\/(\d+)/);
    if (m) return { type: 'movie', id: m[1] };
    // CineSrc TV: /embed/tv/{id}?s=&e= ; inne: /tv/{id}/{s}/{e}
    m = path.match(/\/(?:embed\/)?tv\/(\d+)(?:\/(\d+)\/(\d+))?/);
    if (m) {
      let season = m[2] || '1';
      let episode = m[3] || '1';
      try {
        const q = new URLSearchParams(search);
        if (q.get('s')) season = q.get('s');
        if (q.get('e')) episode = q.get('e');
        if (q.get('season')) season = q.get('season');
        if (q.get('episode')) episode = q.get('episode');
      } catch (e) { /* ignore */ }
      return { type: 'tv', id: m[1], season: season, episode: episode };
    }
    return null;
  }

  function parseFromIframes() {
    for (const f of document.querySelectorAll('iframe[src]')) {
      try {
        const ctx = parseUrl(new URL(f.src, location.href).href);
        if (ctx) return ctx;
      } catch (e) { /* ignore */ }
    }
    return null;
  }

  function ctxKey(ctx) {
    return ctx ? [ctx.type, ctx.id, ctx.season || '', ctx.episode || ''].join('/') : '';
  }

  function storeCtx(ctx) {
    if (!ctx || ctxKey(ctx) === ctxKey(cachedCtx)) return;
    cachedCtx = ctx;
    try { sessionStorage.setItem('ps-media', JSON.stringify(ctx)); } catch (e) { /* ignore */ }
  }

  function loadStoredCtx() {
    if (cachedCtx) return cachedCtx;
    try {
      cachedCtx = JSON.parse(sessionStorage.getItem('ps-media'));
    } catch (e) { cachedCtx = null; }
    return cachedCtx;
  }

  function parseMediaContext() {
    let ctx = parseUrl(location.href);
    if (ctx) { storeCtx(ctx); return ctx; }
    ctx = parseFromIframes();
    if (ctx) { storeCtx(ctx); return ctx; }
    let w = window;
    while (w !== w.top) {
      try {
        w = w.parent;
        ctx = parseUrl(w.location.href);
        if (ctx) { storeCtx(ctx); return ctx; }
      } catch (e) { break; }
    }
    if (document.referrer) {
      try {
        ctx = parseUrl(document.referrer);
        if (ctx) { storeCtx(ctx); return ctx; }
      } catch (e) { /* ignore */ }
    }
    return loadStoredCtx();
  }

  function askTop(msgType, replyType, timeout) {
    return new Promise(resolve => {
      if (window === window.top) { resolve(null); return; }
      let done = false;
      const timer = setTimeout(finish, timeout || 800);
      function onMsg(e) {
        if (e.data?.type === replyType) finish(e.data);
      }
      function finish(payload) {
        if (done) return;
        done = true;
        clearTimeout(timer);
        window.removeEventListener('message', onMsg);
        resolve(payload || null);
      }
      window.addEventListener('message', onMsg);
      window.top.postMessage({ type: msgType }, '*');
    });
  }

  function navigateTo(url) {
    if (window === window.top) {
      location.assign(url);
      return;
    }
    window.top.postMessage({ type: 'ps-switch', url: url }, '*');
  }

  function getPlayers(ctx) {
    // Kolejność = max bitrate (2026-10-28 Verity); VidSrc.to na końcu (pokrycie).
    // Sync z movie-server/players.py
    if (ctx.type === 'movie') {
      return [
        { name: 'VidSrc.su', url: 'https://vidsrc.su/movie/' + ctx.id },
        { name: 'Filmu', url: 'https://embed.filmu.in/movie/' + ctx.id },
        { name: 'VixSrc', url: 'https://vixsrc.to/movie/' + ctx.id },
        { name: 'CineSrc', url: 'https://cinesrc.st/embed/movie/' + ctx.id },
        { name: 'Cinezo', url: 'https://player.cinezo.live/embed/movie/' + ctx.id },
        { name: 'MoviesAPI', url: 'https://moviesapi.to/movie/' + ctx.id },
        { name: 'VidSrc', url: 'https://vidsrc.to/embed/movie/' + ctx.id }
      ];
    }
    return [
      { name: 'VidSrc.su', url: 'https://vidsrc.su/tv/' + ctx.id + '/' + ctx.season + '/' + ctx.episode },
      { name: 'Filmu', url: 'https://embed.filmu.in/tv/' + ctx.id + '/' + ctx.season + '/' + ctx.episode },
      { name: 'VixSrc', url: 'https://vixsrc.to/tv/' + ctx.id + '/' + ctx.season + '/' + ctx.episode },
      { name: 'CineSrc', url: 'https://cinesrc.st/embed/tv/' + ctx.id + '?s=' + ctx.season + '&e=' + ctx.episode },
      { name: 'Cinezo', url: 'https://player.cinezo.live/embed/tv/' + ctx.id + '/' + ctx.season + '/' + ctx.episode },
      { name: 'MoviesAPI', url: 'https://moviesapi.to/tv/' + ctx.id + '/' + ctx.season + '/' + ctx.episode },
      { name: 'VidSrc', url: 'https://vidsrc.to/embed/tv/' + ctx.id + '/' + ctx.season + '/' + ctx.episode }
    ];
  }

  function syncPlayerIdx(href) {
    if (/vidsrc\.su/i.test(href)) { playerIdx = 0; return; }
    if (/filmu\.in|vidly\.pro/i.test(href)) { playerIdx = 1; return; }
    if (/vixsrc\.to/i.test(href)) { playerIdx = 2; return; }
    if (/cinesrc\.st/i.test(href)) { playerIdx = 3; return; }
    if (/player\.cinezo\.live/i.test(href)) { playerIdx = 4; return; }
    if (/moviesapi\.to/i.test(href)) { playerIdx = 5; return; }
    if (/vidsrc\.to/i.test(href)) { playerIdx = 6; return; }
    playerIdx = 0; // nieznany URL -> domyślnie pierwszy (VidSrc.su)
  }

  async function resolvePlayers() {
    let ctx = parseMediaContext();
    if (!ctx) {
      const rep = await askTop('ps-get-context', 'ps-context');
      if (rep?.ctx) { ctx = rep.ctx; storeCtx(ctx); }
    }
    if (!ctx) return null;
    return getPlayers(ctx);
  }

  async function selectPlayer(idx) {
    const players = await resolvePlayers();
    if (!players || !players[idx]) return;
    playerIdx = idx;
    navigateTo(players[idx].url);
  }

  async function currentPlayerIdx() {
    let href = location.href;
    if (window !== window.top) {
      const rep = await askTop('ps-get-href', 'ps-href');
      if (rep?.href) href = rep.href;
    }
    syncPlayerIdx(href);
    return playerIdx;
  }

  function makePlayerSelect() {
    const sel = document.createElement('select');
    sel.id = 'ps-player-select';
    sel.style.cssText =
      'height:34px;font-size:13px;font-weight:bold;background:#1565ff;color:#fff;' +
      'border:none;border-radius:6px;cursor:pointer;opacity:.85;padding:0 4px;';
    sel.onclick = e => e.stopPropagation();
    sel.onchange = e => {
      e.stopPropagation();
      selectPlayer(Number(sel.value));
    };
    resolvePlayers().then(players => {
      if (!players) return;
      sel.dataset.ctx = ctxKey(cachedCtx);
      sel.innerHTML = '';
      players.forEach((p, i) => {
        const opt = document.createElement('option');
        opt.value = String(i);
        opt.textContent = p.name;
        sel.appendChild(opt);
      });
      currentPlayerIdx().then(idx => { sel.value = String(idx); });
    });
    return sel;
  }

  function buildUI() {
    if (document.getElementById('ps-ctrl')) return;
    const root = document.body || document.documentElement;
    if (!root) return;
    const box = document.createElement('div');
    box.id = 'ps-ctrl';
    box.style.cssText =
      'position:fixed;top:10px;right:10px;z-index:2147483647;display:flex;gap:4px;';
    box.appendChild(makeBtn('A', autoZoom));
    box.appendChild(makeBtn('+', () => { scale += 0.1; applyScale(); }));
    box.appendChild(makeBtn('-', () => { scale = Math.max(0.5, scale - 0.1); applyScale(); }));
    box.appendChild(makeBtn('0', () => { scale = 1; applyScale(); }));
    box.appendChild(makePlayerSelect());
    root.appendChild(box);
  }

  function tick() {
    const ctx = parseMediaContext();
    if (findVideo()) {
      buildUI();
      // SPA: zmiana odcinka bez przeładowania — przebuduj listę playerów.
      const sel = document.getElementById('ps-player-select');
      if (sel && ctx && sel.dataset.ctx && sel.dataset.ctx !== ctxKey(ctx)) {
        sel.replaceWith(makePlayerSelect());
      }
      applyScale();
    } else {
      document.getElementById('ps-ctrl')?.remove();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', tick);
  } else {
    tick();
  }
  setInterval(tick, 1000);
})();