#!/usr/bin/env node
// Natywny klient WebDriver BiDi (Firefox) — WebSocket, bez Selenium/Playwright.
// WebDriver BiDi to oficjalny standard W3C (nowszy niż Marionette, wsparty też
// przez Chrome/Chromium) — JSON przez zwykły WebSocket, obsługiwany natywnym
// `WebSocket` w Node 21+ bez żadnej biblioteki.
//
// Wymaga uruchomienia Firefoksa z flagą:
//   firefox --remote-debugging-port=9222 --no-remote
//
// Endpoint sesji: ws://127.0.0.1:9222/session
//
// Użycie jako CLI:
//   node tools/bidi.js install-addon <ścieżka.xpi>
//   node tools/bidi.js navigate <url>
//   node tools/bidi.js eval "<js>"
//
// Użycie jako moduł:
//   const { BidiClient } = require('./tools/bidi');
//   const client = new BidiClient();
//   await client.connect();
//   await client.newSession();
//   await client.navigate('https://example.com');
//
// Znane ograniczenie (sprawdzone empirycznie, 2026-09-13): sesje BiDi nie
// przechwytują nawigacji do plików .user.js przez Tampermonkey tak jak zwykła,
// ręcznie uruchomiona sesja Firefoksa — okno instalacji userscriptu się nie
// pojawia. Instalacja samego rozszerzenia (installAddon) działa bez problemu.
// To osobne zabezpieczenie od tego, które blokuje ExecuteScript na stronach
// uprzywilejowanych w Marionette (tools/marionette.js) — w obu przypadkach
// efekt jest ten sam: zainstalowanie konkretnego userscriptu do Tampermonkeya
// wymaga ręcznego kliknięcia "Zainstaluj"/"Przeinstaluj" przez użytkownika,
// niezależnie od protokołu automatyzacji.

class BidiClient {
  constructor({ port = 9222, host = '127.0.0.1' } = {}) {
    this.url = `ws://${host}:${port}/session`;
    this.ws = null;
    this.msgId = 0;
    this.pending = new Map();
    this.sessionId = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (e) => reject(new Error(`WebSocket error: ${JSON.stringify(e)}`));
      this.ws.onmessage = (e) => this._onMessage(e);
    });
  }

  _onMessage(event) {
    const msg = JSON.parse(event.data);
    if (msg.id !== undefined && this.pending.has(msg.id)) {
      const p = this.pending.get(msg.id);
      this.pending.delete(msg.id);
      if (msg.type === 'success') p.resolve(msg.result);
      else p.reject(msg);
    }
    // Zdarzenia bez `id` (np. subskrypcje) są celowo ignorowane — ten klient
    // obsługuje tylko wywołania request/response.
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.msgId++;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async newSession(capabilities = {}) {
    const result = await this.send('session.new', { capabilities });
    this.sessionId = result.sessionId;
    return result;
  }

  async getTree() {
    return this.send('browsingContext.getTree', {});
  }

  async navigate(url, { context, wait = 'complete' } = {}) {
    const ctx = context || (await this._firstContext());
    return this.send('browsingContext.navigate', { context: ctx, url, wait });
  }

  async evaluate(expression, { context, awaitPromise = false } = {}) {
    const ctx = context || (await this._firstContext());
    return this.send('script.evaluate', {
      expression,
      target: { context: ctx },
      awaitPromise,
    });
  }

  // path: ścieżka lokalna do pliku .xpi.
  async installAddon(path) {
    return this.send('webExtension.install', {
      extensionData: { type: 'path', path },
    });
  }

  async _firstContext() {
    const tree = await this.getTree();
    return tree.contexts[0].context;
  }

  // Kończy sesję WebDriver po stronie serwera. Bez tego Firefox trzyma sesję
  // aktywną nawet po zamknięciu WebSocketu (limit "Maximum number of active
  // sessions" ujawnia się dopiero przy kolejnym połączeniu).
  async endSession() {
    if (!this.sessionId) return;
    await this.send('session.end', {}).catch(() => {});
  }

  close() {
    this.ws.close();
  }
}

async function main() {
  const [, , cmd, ...rest] = process.argv;
  if (!cmd) {
    console.error('Użycie: node tools/bidi.js <install-addon|navigate|eval> <arg>');
    process.exit(1);
  }

  const client = new BidiClient();
  await client.connect();
  await client.newSession();

  try {
    if (cmd === 'install-addon') {
      const [path] = rest;
      const result = await client.installAddon(path);
      console.log(JSON.stringify(result, null, 2));
    } else if (cmd === 'navigate') {
      const [url] = rest;
      const result = await client.navigate(url);
      console.log(JSON.stringify(result, null, 2));
    } else if (cmd === 'eval') {
      const [expression] = rest;
      const result = await client.evaluate(expression);
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.error(`Nieznana komenda: ${cmd}`);
      process.exitCode = 1;
    }
  } finally {
    await client.endSession();
    client.close();
  }
}

if (require.main === module) {
  main().catch((err) => {
    console.error('FATAL:', err);
    process.exit(1);
  });
}

module.exports = { BidiClient };
