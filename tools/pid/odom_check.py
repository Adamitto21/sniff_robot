#!/usr/bin/env python3
"""
SNIFF — weryfikacja kalibracji odometrii (ONE_CIRCLE_PLUSES).

Jedzie prosto zadanym PWM przez zadany czas, całkuje prędkości z enkoderów
i podaje przejechany dystans wg robota. Porównujesz z pomiarem miarką.

    python3 odom_check.py --pwm 130 --czas 4

Procedura:
  1. Zaznacz punkt startowy (taśma na podłodze przy konkretnym kole).
  2. Uruchom skrypt. Robot rusza po 3 s (zdążysz się odsunąć).
  3. Zmierz miarką faktyczny dystans i porównaj z wynikiem.
  4. Nowe ONE_CIRCLE_PLUSES = stare * (dystans_wg_robota / dystans_rzeczywisty)

UWAGA: potrzeba ok. 3 m wolnej przestrzeni. Zatrzymaj platform_driver.
"""
import argparse
import json
import sys
import time

import serial

BOOT_WAIT_S = 4.0
READY_TIMEOUT_S = 30.0


def send(ser, obj):
    ser.write((json.dumps(obj) + "\n").encode())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", default="/dev/ttyCH343USB0")
    ap.add_argument("--pwm", type=int, default=130, help="PWM jazdy (80-180)")
    ap.add_argument("--czas", type=float, default=4.0, help="czas jazdy [s]")
    ap.add_argument("--out", default="odom_check.csv")
    args = ap.parse_args()

    ser = serial.Serial()
    ser.port, ser.baudrate, ser.timeout = args.port, 115200, 0.05
    ser.dtr = False
    ser.rts = False
    ser.exclusive = True
    ser.open()
    print(f"[i] Czekam {BOOT_WAIT_S} s na start ESP32...")
    time.sleep(BOOT_WAIT_S)
    ser.reset_input_buffer()

    # czekaj na gotowość
    t0 = time.monotonic()
    ready = False
    while time.monotonic() - t0 < READY_TIMEOUT_S and not ready:
        send(ser, {"T": 143, "cmd": 0})
        send(ser, {"T": 142, "cmd": 0})
        send(ser, {"T": 131, "cmd": 1})
        send(ser, {"T": 130})
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            line = ser.readline()
            if line and b"1001" in line:
                ready = True
                break
    if not ready:
        print("[!] ESP32 nie odpowiada."); ser.close(); return 1
    print("[i] Gotowy.")

    for i in (3, 2, 1):
        print(f"    start za {i}...")
        time.sleep(1.0)

    dist_L = dist_R = 0.0
    rows = []
    t_prev = None
    t_start = time.monotonic()
    last_ka = t_start
    try:
        send(ser, {"T": 11, "L": args.pwm, "R": args.pwm})
        while time.monotonic() - t_start < args.czas:
            now = time.monotonic()
            if now - last_ka > 0.8:
                send(ser, {"T": 11, "L": args.pwm, "R": args.pwm})
                last_ka = now
            line = ser.readline()
            if not line:
                continue
            try:
                d = json.loads(line.decode(errors="ignore").strip())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(d, dict) or d.get("T") != 1001:
                continue
            vL, vR = float(d.get("L", 0)), float(d.get("R", 0))
            if t_prev is not None:
                dt = now - t_prev
                dist_L += vL * dt
                dist_R += vR * dt
            t_prev = now
            rows.append([round(now - t_start, 4), vL, vR,
                         round(dist_L, 4), round(dist_R, 4)])
    finally:
        send(ser, {"T": 11, "L": 0, "R": 0})
        ser.flush()
        time.sleep(0.3)
        send(ser, {"T": 131, "cmd": 0})
        ser.flush()
        time.sleep(0.2)
        ser.close()

    if not rows:
        print("[!] Brak danych."); return 1

    import csv
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "vL", "vR", "dist_L", "dist_R"])
        w.writerows(rows)

    avg = (dist_L + dist_R) / 2
    print("\n" + "=" * 52)
    print(f"  Dystans wg lewego enkodera : {dist_L:.3f} m")
    print(f"  Dystans wg prawego enkodera: {dist_R:.3f} m")
    print(f"  Średnia                    : {avg:.3f} m")
    print(f"  Średnia prędkość           : {avg / args.czas:.3f} m/s")
    print("=" * 52)
    print("\n  Zmierz miarką rzeczywisty dystans i policz:")
    print("     nowe_ONE_CIRCLE_PLUSES = 1650 * (wynik_wyzej / dystans_rzeczywisty)")
    print(f"  Np. jesli robot przejechal 2.00 m, a wyzej jest {avg:.2f} m:")
    print(f"     1650 * {avg:.3f}/2.00 = {1650 * avg / 2.0:.0f}")
    print(f"\n  Dane: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
