#!/usr/bin/env python3
"""
SNIFF — diagnostyka komunikacji z ESP32 (UGV02).

Rozstrzyga, dlaczego nie przychodzą ramki T:1001. Nie steruje silnikami — bezpieczny.

    python3 ugv_diag.py                     # bez resetu płytki (jeśli już wystartowała)
    python3 ugv_diag.py --reset             # wymuś reset i zmierz czas bootowania

Co robi:
  TEST 0 — zbiera surowe linie z portu (komunikaty debug firmware)
  TEST 1 — odpytywanie {"T":130}: czy loop() w ogóle się wykonuje i jak szybko
  TEST 2 — strumień {"T":131,"cmd":1}: czy działa tryb ciągły i z jaką częstotliwością
  WERDYKT — interpretacja + co robić dalej
"""
import argparse
import json
import statistics as st
import sys
import time

import serial

READY_TIMEOUT_S = 40.0


def open_serial(port, baud, do_reset):
    ser = serial.Serial()
    ser.port, ser.baudrate, ser.timeout = port, baud, 0.05
    # dtr/rts wysoko = reset płytki przy otwarciu; nisko = próba uniknięcia resetu
    ser.dtr = bool(do_reset)
    ser.rts = bool(do_reset)
    ser.exclusive = True
    ser.open()
    return ser


def read_lines(ser, duration_s):
    """Czyta przez zadany czas, zwraca (ramki_1001, surowe_linie_inne)."""
    frames, raw = [], []
    t_end = time.monotonic() + duration_s
    while time.monotonic() < t_end:
        line = ser.readline()
        if not line:
            continue
        txt = line.decode(errors="ignore").strip()
        if not txt:
            continue
        try:
            d = json.loads(txt)
        except json.JSONDecodeError:
            raw.append((round(time.monotonic(), 3), txt))
            continue
        if isinstance(d, dict) and d.get("T") == 1001:
            frames.append((time.monotonic(), d))
        else:
            raw.append((round(time.monotonic(), 3), txt))
    return frames, raw


def send(ser, obj):
    ser.write((json.dumps(obj) + "\n").encode())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", default="/dev/ttyCH343USB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--reset", action="store_true",
                    help="wymuś reset ESP32 (DTR/RTS) i zmierz czas bootowania")
    args = ap.parse_args()

    print("=" * 62)
    print("SNIFF — diagnostyka ESP32")
    print("=" * 62)

    try:
        ser = open_serial(args.port, args.baud, args.reset)
    except Exception as e:
        print(f"[!] Nie mogę otworzyć {args.port}: {e}")
        print("    Zajęty? sprawdź:  sudo fuser -v " + args.port)
        return 1
    print(f"[i] Port {args.port} otwarty (reset płytki: "
          f"{'TAK' if args.reset else 'nie'})")

    # ---------- TEST 0: co płytka wypisuje sama z siebie ----------
    print("\n--- TEST 0: nasłuch 8 s (komunikaty własne firmware) ---")
    frames0, raw0 = read_lines(ser, 8.0)
    if raw0:
        print(f"  Odebrano {len(raw0)} linii nie-JSON. Pierwsze 15:")
        for t, txt in raw0[:15]:
            print(f"    {txt[:100]}")
        spam = [t for t, x in raw0 if "Waiting Sensor" in x or "fail" in x.lower()]
        if spam:
            print(f"  >>> UWAGA: {len(spam)} linii o błędzie czujnika "
                  f"(IMU/magnetometr) — to spowalnia loop().")
    else:
        print("  Brak komunikatów tekstowych (to normalne po zakończeniu bootu).")
    if frames0:
        print(f"  Odebrano też {len(frames0)} ramek T:1001 "
              f"(strumień był już włączony).")

    # ---------- oczekiwanie na gotowość ----------
    print("\n--- Czekam na odpowiedź na {\"T\":130} ---")
    t0 = time.monotonic()
    ready = False
    while time.monotonic() - t0 < READY_TIMEOUT_S and not ready:
        send(ser, {"T": 143, "cmd": 0})
        send(ser, {"T": 130})
        f, _ = read_lines(ser, 1.0)
        if f:
            ready = True
    if not ready:
        print(f"[!] Brak odpowiedzi przez {READY_TIMEOUT_S:.0f} s.")
        print("    -> płytka nie przetwarza komend. Sprawdź monitorem:")
        print(f"       arduino-cli monitor -p {args.port} -c baudrate=115200")
        ser.close()
        return 1
    boot_s = time.monotonic() - t0
    print(f"  Płytka odpowiada (po {boot_s:.1f} s).")

    # ---------- TEST 1: odpytywanie ----------
    print("\n--- TEST 1: odpytywanie {\"T\":130} co 300 ms przez 6 s ---")
    send(ser, {"T": 131, "cmd": 0})   # strumień OFF, żeby nie mieszał
    time.sleep(0.5)
    ser.reset_input_buffer()
    lat, got = [], 0
    for _ in range(20):
        t_send = time.monotonic()
        send(ser, {"T": 130})
        f, _ = read_lines(ser, 0.3)
        if f:
            got += 1
            lat.append((f[0][0] - t_send) * 1000)
    print(f"  Odpowiedzi: {got}/20")
    if lat:
        print(f"  Opóźnienie: śr {st.mean(lat):.0f} ms, max {max(lat):.0f} ms")

    # ---------- TEST 2: strumień ----------
    print("\n--- TEST 2: strumień {\"T\":131,\"cmd\":1} przez 6 s ---")
    send(ser, {"T": 142, "cmd": 0})   # bez dodatkowego opóźnienia
    send(ser, {"T": 131, "cmd": 1})
    time.sleep(0.3)
    ser.reset_input_buffer()
    frames2, raw2 = read_lines(ser, 6.0)
    hz = len(frames2) / 6.0
    print(f"  Ramek: {len(frames2)} w 6 s -> {hz:.1f} Hz")
    if frames2:
        d = frames2[-1][1]
        print(f"  Ostatnia ramka: L={d.get('L')} R={d.get('R')} "
              f"v={d.get('v')} y={d.get('y')}")
    send(ser, {"T": 131, "cmd": 0})
    ser.flush()
    time.sleep(0.2)
    ser.close()

    # ---------- WERDYKT ----------
    print("\n" + "=" * 62)
    print("WERDYKT")
    print("=" * 62)
    loop_hz = got / 6.0 if got else 0
    if hz >= 20:
        print("  Komunikacja OK — strumień działa z sensowną częstotliwością.")
        print("  -> Wracaj do pid_step_test.py, problem był przejściowy.")
    elif hz >= 1 or loop_hz >= 1:
        print(f"  Płytka odpowiada, ale WOLNO (strumień {hz:.1f} Hz).")
        print("  -> loop() jest spowolniony. Najczęstsze przyczyny, po kolei:")
        print("     1. ArduinoJson 7.x zamiast 6.x  (sprawdź: arduino-cli lib list)")
        print("     2. brak odpowiedzi IMU/magnetometru na I2C (timeouty w loop)")
        print("     3. tryb WiFi AP + serwer HTTP")
    else:
        print("  Płytka odpowiada tylko na pojedyncze zapytania, strumień NIE działa.")
        print("  -> sprawdź wersję firmware i czy upload faktycznie się powiódł.")
    print(f"\n  Czas do pierwszej odpowiedzi: {boot_s:.1f} s "
          f"(zdrowo: < 3 s; > 10 s = problem z inicjalizacją peryferiów)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
