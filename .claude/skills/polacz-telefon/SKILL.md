---
name: polacz-telefon
description: Połącz się z telefonem Android przez ADB, żeby sprawdzić zainstalowane aplikacje, pobrać pliki (np. zrzuty ekranu) i podstawowe informacje o urządzeniu. Użyj, gdy użytkownik pyta o coś związane z telefonem (np. "sprawdź czy mam X na telefonie", "pobierz mój ostatni zrzut ekranu") zamiast od razu odpowiadać, że nie masz dostępu.
---

# Połączenie z telefonem przez ADB

Telefon bywa podłączony fizycznie (USB) z włączonym debugowaniem USB. Wtedy `adb`
(Android Platform Tools) daje ograniczony, ale realny wgląd w urządzenie — **nie**
"brak jakiegokolwiek dostępu", jak można by założyć domyślnie.

## Krok 0: sprawdź, czy telefon jest w ogóle podłączony

```
adb devices
```

- Brak wpisu → telefon nie jest podłączony/USB debugging wyłączone. Nie da się nic
  więcej zrobić — poproś użytkownika o podłączenie kablem i włączenie debugowania USB
  (Ustawienia → Opcje programistyczne → Debugowanie USB), potem zatwierdzenie okna
  na telefonie.
- Stan `unauthorized` → poproś o zatwierdzenie okna na ekranie telefonu.
- Stan `device` → telefon jest gotowy do dalszych poleceń.

Jeśli `adb` nie jest zainstalowany, poszukaj Platform Tools (np. w
`AppData/Local/Microsoft/WinGet/Packages/...platform-tools/adb.exe` na Windows) albo
poproś użytkownika o instalację.

## Co da się sprawdzić

- **Lista zainstalowanych aplikacji:**
  ```
  adb shell pm list packages | grep -i <fragment_nazwy>
  ```
  Telefon może mieć wiele profili (`adb shell pm list users`) — np. profil główny `0`
  i profil służbowy/Work profile. Domyślne polecenia bez `--user` odpytują tylko
  bieżący/domyślny profil; profil służbowy bywa niedostępny z poziomu shell
  (`SecurityException`) — to oczekiwane ograniczenie, nie błąd do obchodzenia.

- **Podstawowe info o urządzeniu:** model, wersja Androida, itp.:
  ```
  adb shell getprop ro.product.model
  adb shell getprop ro.build.version.release
  ```

- **Logi aplikacji, jeśli własna apka i debuggable:**
  ```
  adb shell run-as <package> ...
  ```
  Działa **tylko** dla aplikacji zbudowanych jako `debuggable` (typowo własne apki w
  wersji debug). Dla aplikacji produkcyjnych ze Sklepu Play (Firefox, Chrome, banki
  itd.) `run-as` zwraca `package not debuggable` — to twarde zabezpieczenie systemu
  Android, którego nie da się ominąć bez roota. Nie próbuj obchodzić.

## Czego NIE da się sprawdzić w ten sposób

- **Wnętrza danych aplikacji produkcyjnych** (np. które rozszerzenia ma zainstalowane
  Firefox, jego profile, ciasteczka, hasła) — dane te leżą w prywatnym katalogu
  aplikacji (`/data/data/<package>/`), niedostępnym bez roota dla aplikacji, która nie
  jest `debuggable`. Samo `pm list packages` potwierdzi tylko, **czy** apka jest
  zainstalowana, nie co jest w jej wnętrzu.
- Dla pytań w stylu "jakie rozszerzenia mam w Tampermonkey/Firefoksie" — jedyna droga
  to poprosić użytkownika o zrzut ekranu, eksport z poziomu samej aplikacji (np.
  Tampermonkey Dashboard → Utilities → Export), albo wklejony tekst/kod.

## Kiedy używać tego skilla

Gdy użytkownik pyta o coś związanego z telefonem, **najpierw** sprawdź `adb devices` —
dopiero jeśli telefon faktycznie nie jest podłączony albo dane są w niedostępnej
sandboxie aplikacji, wyjaśnij ograniczenie i poproś o alternatywną drogę (zrzut ekranu,
eksport, wklejony tekst).
