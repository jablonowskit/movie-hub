---
name: testuj-userscript-bidi
description: Zweryfikuj automatycznie, czy userscript Tampermonkey działa poprawnie na danej stronie (np. czy pojawia się UI, czy wykrywa <video>, jaki jest efekt kliknięcia) — bez ręcznego klikania w przeglądarce. Użyj po każdej zmianie w pliku .user.js, zanim poprosisz użytkownika o ręczne potwierdzenie.
---

# Testowanie userscriptu przez WebDriver BiDi

Firefox nie ma odpowiednika Chrome DevTools Protocol (CDP) — ma własny,
natywny standard **WebDriver BiDi** (WebSocket + JSON, W3C). Ten projekt ma
gotowy, zależny wyłącznie od wbudowanego `WebSocket` w Node (21+) klient:
[`tools/bidi.js`](../../tools/bidi.js).

## Krok 0: uruchom Firefoksa z portem debugowania

```
taskkill //F //IM firefox.exe   # zamknij stare instancje, inaczej port bywa zajęty
"C:/Program Files/Mozilla Firefox/firefox.exe" --remote-debugging-port=9222 --no-remote &
sleep 5
```

Sprawdź, że port nasłuchuje: `netstat -an | grep 9222`.

**Ważne:** jeśli test ma sprawdzać działanie zainstalowanego rozszerzenia
(Tampermonkey + userscript), uruchom Firefoksa na profilu, w którym te
rozszerzenia faktycznie są aktywne (`-P <nazwa_profilu>`), inaczej sesja BiDi
może wylądować na innym/domyślnym profilu bez rozszerzeń.

## Krok 1: napisz mały skrypt testowy

```js
const { BidiClient } = require('D:/github/skryptyjs/tools/bidi.js');

(async () => {
  const client = new BidiClient();
  await client.connect();
  await client.newSession();

  await client.navigate('https://example.com/strona-z-video');
  await new Promise(r => setTimeout(r, 3000)); // czas na content-script

  const result = await client.evaluate(`
    (() => {
      const ctrl = document.getElementById('ps-ctrl');
      const video = document.querySelector('video');
      return JSON.stringify({ hasVideo: !!video, hasCtrlUI: !!ctrl });
    })()
  `);
  console.log(result.result.value);

  await client.endSession(); // ważne — patrz "Pułapka" niżej
  client.close();
  process.exit(0);
})();
```

Uruchom z twardym timeoutem procesu, żeby zawieszona strona nie zablokowała
Cię w nieskończoność: `timeout 20 node test.js`.

## Pułapka: limit sesji BiDi

`session.new` tworzy trwałą sesję po stronie Firefoksa. Samo zamknięcie
WebSocketu (`client.close()`) **nie** kończy tej sesji — kolejne
`session.new` w tym samym uruchomieniu Firefoksa dostanie
`"Maximum number of active sessions"`. Zawsze wywołuj `client.endSession()`
przed `client.close()` (już wbudowane w `tools/bidi.js`), albo między testami
restartuj Firefoksa.

## Pułapka: strony z ochroną antybot (DDoS-Guard/Cloudflare) dają fałszywe negatywy

Automatyzowana sesja BiDi bywa wykrywana i serwowana inaczej niż zwykła sesja
użytkownika — strona może nie załadować treści wcale (pusty `<body>`,
`hasVideo: false`), mimo że w normalnej przeglądarce działa. Traktuj wynik
`false`/pusty jako **niepewny**, nie jako dowód, że coś jest zepsute —
zweryfikuj też ręcznie albo zapytaj użytkownika, zanim wyciągniesz wniosek.
Odwrotnie: wynik `true` (rzeczywisty `<video>` z niepustym `videoSrc`, np.
`blob:...`) jest wiarygodnym dowodem, że strona faktycznie odtwarza.

## Pułapka: `curl` bywa zawodny dla tych samych stron

Te same strony antybotowe często zwracają `curl`-owi 404/pustkę, nawet gdy
prawdziwa przeglądarka (i BiDi) dostają poprawną treść — `curl` nie ma
ciasteczek/nagłówków, które ochrona wymaga. Nie ufaj samemu kodowi HTTP z
`curl` przy diagnozowaniu stron streamingowych/antybotowych; zawsze
zweryfikuj przez realną (lub BiDi) sesję przeglądarki.

## Pułapka: sekwencyjne testy wielu URL w jednej pętli bywają wolne/niestabilne

Restart Firefoksa + nowa sesja per URL jest bezpieczniejszy niż jeden długo
żyjący klient odwiedzający wiele stron pod rząd (jedna zawieszona strona może
ubić całą pętlę). Jeśli testujesz > 5 adresów, rozważ osobny proces Node per
URL z zewnętrznym `timeout`, i loguj wynik do pliku na bieżąco (nie czekaj na
koniec całej pętli, żeby zobaczyć postęp) — patrz `results2.log` z sesji
2026-09-13 jako wzorzec.
