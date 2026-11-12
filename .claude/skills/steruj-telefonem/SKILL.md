---
name: steruj-telefonem
description: Sterowanie podłączonym telefonem Android przez ADB (kliknięcia, gesty/swipe, klawisze, wybudzanie, wprowadzanie tekstu, zrzuty ekranu, uruchamianie aplikacji i URL-i). Użyj, gdy trzeba przetestować aplikację lub stronę bezpośrednio na telefonie, odświeżyć widok, przewinąć stronę lub sprawdzić stan interfejsu.
---

# Sterowanie telefonem Android przez ADB

Gdy telefon jest podłączony przez USB/WiFi z włączonym debugowaniem USB (`adb devices` pokazuje stan `device`), można w pełni symulować interakcję użytkownika i automatyzować testowanie stron i aplikacji.

## 1. Weryfikacja połączenia i ekranu

Zawsze zaczynaj od sprawdzenia dostępności urządzenia i jego rozdzielczości:

```bash
adb devices
adb shell wm size       # np. Physical size: 1080x2340
adb shell wm density    # np. Physical density: 450, Override density: 480
```

Współrzędne kliknięć (`tap`) i przeciągnięć (`swipe`) podaje się w pikselach fizycznych (`wm size`), gdzie `(0, 0)` to lewy górny róg.

---

## 2. Zrzut ekranu (Screenshot)

Do analizy stanu interfejsu używaj zapisu do `/sdcard/` i pobrania przez `adb pull`:

```bash
# Bezpieczne pobranie zrzutu (unika problemów z kodowaniem znaków w PowerShellu):
adb shell screencap -p /sdcard/screen.png
adb pull /sdcard/screen.png ./screen.png
adb shell rm /sdcard/screen.png
```

---

## 3. Wybudzanie i blokada ekranu

```bash
# Wybudzenie ekranu (jeśli jest uśpiony/zgaszony):
adb shell input keyevent 224    # KEYCODE_WAKEUP

# Przesunięcie w górę, aby odblokować ekran (jeśli nie ma kodu PIN):
adb shell input swipe 540 1800 540 500 200

# Zablokowanie/uśpienie ekranu:
adb shell input keyevent 26     # KEYCODE_POWER (lub 223 KEYCODE_SLEEP)
```

---

## 4. Klikanie i gesty (Tap & Swipe)

```bash
# Pojedyncze kliknięcie w punkt (X, Y):
adb shell input tap 540 1000

# Długie przytrzymanie (swipe z tego samego punktu z długim czasem trwania w ms):
adb shell input swipe 540 1000 540 1000 1000

# Przewinięcie w dół (palec w górę):
adb shell input swipe 540 1600 540 400 300

# Przewinięcie w górę (palec w dół):
adb shell input swipe 540 400 540 1600 300

# Przeciągnięcie od lewej/prawej krawędzi (np. cofanie gestem):
adb shell input swipe 10 1000 400 1000 150
```

---

## 5. Klawisze sprzętowe i nawigacyjne (Keyevents)

```bash
# Wstecz (Back):
adb shell input keyevent 4

# Ekran główny (Home):
adb shell input keyevent 3

# Przełącznik ostatnich aplikacji (Recent Apps):
adb shell input keyevent 187    # KEYCODE_APP_SWITCH

# Enter:
adb shell input keyevent 66

# Spacja:
adb shell input keyevent 62

# Usuń znak (Backspace):
adb shell input keyevent 67

# Tab:
adb shell input keyevent 61
```

---

## 6. Wprowadzanie tekstu

```bash
# Wpisanie tekstu do aktywnego pola:
adb shell input text "wyszukiwana_fraza"

# Uwaga: spacje w 'input text' zastępuje się %s:
adb shell input text "tytul%sfilmu"
```

---

## 7. Sterowanie przeglądarką i aplikacjami

### Uruchomienie adresu URL w Firefoksie:
```bash
adb shell am start -a android.intent.action.VIEW -d "http://192.168.55.1:9000/" -p org.mozilla.firefox
```

### Uruchomienie adresu URL w domyślnej przeglądarce:
```bash
adb shell am start -a android.intent.action.VIEW -d "http://192.168.55.1:9000/"
```

### Wymuszenie restartu aplikacji (zabicie i ponowne otwarcie - przydatne do odświeżenia cache):
```bash
adb shell am force-stop org.mozilla.firefox
adb shell am start -a android.intent.action.VIEW -d "http://192.168.55.1:9000/" -p org.mozilla.firefox
```

---

## 8. Typowy cykl diagnostyczny podczas pracy z UI

1. Zrób screenshot: `adb shell screencap -p /sdcard/s.png; adb pull /sdcard/s.png ./s.png`.
2. Zobacz plik za pomocą narzędzia `view_file`.
3. Wyznacz potrzebne współrzędne elementów na podstawie zrzutu i rozdzielczości ekranu.
4. Wykonaj akcję (`input tap`, `input swipe` lub `input text`).
5. Zrób kolejny screenshot, aby zweryfikować rezultat działania.
