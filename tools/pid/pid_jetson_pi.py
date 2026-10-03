#!/usr/bin/env python3
"""
SNIFF — ścieżka B: dyskretny regulator PI prędkości kół liczony NA JETSONIE.

Nie wymaga modyfikacji firmware. Pętla: feedback {"T":1001} (enkodery) ->
PI (50 Hz, antywindup przez clamping wyjścia i całki) -> {"T":11,PWM}.
Loguje CSV zgodny z pid_compare.py (kolumna cmd = wartość zadana [m/s]).

Przykład (skok 0.15 -> 0.35 m/s, nastawy z pid_identify.py):
  python3 pid_jetson_pi.py --kp 310 --ki 1150 \
      --amp0 0.15 --t0 3 --amp1 0.35 --t1 4 --out krok_jetson.csv

Uwaga do raportu PUR: okres pętli i jitter (wypisywane na końcu) to jawne,
mierzalne opóźnienie w torze regulacji — materiał do rozdziału o ograniczeniach.
"""
import argparse
import csv
import json
import sys
import time

import serial

PWM_MAX = 255.0
BOOT_WAIT_S = 3.0  # ESP32 resetuje się przy otwarciu portu (DTR/RTS)
READY_TIMEOUT_S = 25.0  # boot z WiFi AP potrafi trwać kilkanaście sekund


def open_serial(port, baud, timeout=0.005):
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = timeout
    ser.dtr = False
    ser.rts = False
    ser.exclusive = True
    ser.open()
    print(f"[i] Port otwarty, czekam {BOOT_WAIT_S:.1f} s na start ESP32...")
    time.sleep(BOOT_WAIT_S)
    ser.reset_input_buffer()
    return ser


def send(ser, obj):
    ser.write((json.dumps(obj) + "\n").encode())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", default="/dev/ttyCH343USB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--kp", type=float, required=True, help="[PWM/(m/s)]")
    ap.add_argument("--ki", type=float, required=True, help="[PWM/(m/s)/s] (= Kp/Ti)")
    ap.add_argument("--rate", type=float, default=50.0, help="częstotliwość pętli [Hz]")
    ap.add_argument("--amp0", type=float, default=0.0)
    ap.add_argument("--t0", type=float, default=2.0)
    ap.add_argument("--amp1", type=float, required=True)
    ap.add_argument("--t1", type=float, default=4.0)
    ap.add_argument("--out", default="krok_jetson.csv")
    args = ap.parse_args()

    dt_nom = 1.0 / args.rate
    ser = open_serial(args.port, args.baud)

    # aktywne czekanie na gotowość (komendy wysłane w trakcie setup() przepadają)
    print("[i] Czekam na gotowość ESP32...")
    t_ready = time.monotonic()
    ready = False
    while time.monotonic() - t_ready < READY_TIMEOUT_S and not ready:
        send(ser, {"T": 143, "cmd": 0})
        send(ser, {"T": 142, "cmd": 10})
        send(ser, {"T": 131, "cmd": 1})
        send(ser, {"T": 130})
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            line = ser.readline()
            if line and b'"T"' in line and b'1001' in line:
                ready = True
                break
    if not ready:
        print("[!] ESP32 nie odpowiada — port zajęty albo zły /dev/tty*.")
        ser.close()
        return 1
    print(f"[i] Gotowy po {time.monotonic() - t_ready:.1f} s.")
    ser.reset_input_buffer()

    vL = vR = 0.0
    intL = intR = 0.0
    rows, periods = [], []
    t_start = time.monotonic()
    t_last = t_start

    def read_feedback():
        nonlocal vL, vR
        vbat = None
        while True:
            line = ser.readline()
            if not line:
                return vbat
            try:
                d = json.loads(line.decode(errors="ignore").strip())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(d, dict) and d.get("T") == 1001:
                vL = float(d.get("L", vL)); vR = float(d.get("R", vR))
                vbat = d.get("v")

    try:
        for sp, dur in ((args.amp0, args.t0), (args.amp1, args.t1)):
            phase_end = time.monotonic() + dur
            while time.monotonic() < phase_end:
                loop_t0 = time.monotonic()
                dt = loop_t0 - t_last
                t_last = loop_t0
                periods.append(dt)

                vbat = read_feedback()

                uL_raw = uR_raw = 0.0
                for wheel in ("L", "R"):
                    v = vL if wheel == "L" else vR
                    integ = intL if wheel == "L" else intR
                    e = sp - v
                    u_unsat = args.kp * e + integ + args.ki * e * dt
                    u = max(-PWM_MAX, min(PWM_MAX, u_unsat))
                    if u == u_unsat:              # antywindup: całkuj tylko bez nasycenia
                        integ += args.ki * e * dt
                    integ = max(-PWM_MAX, min(PWM_MAX, integ))
                    if wheel == "L":
                        intL, uL_raw = integ, u
                    else:
                        intR, uR_raw = integ, u

                send(ser, {"T": 11, "L": int(round(uL_raw)), "R": int(round(uR_raw))})
                rows.append([round(loop_t0 - t_start, 4), sp,
                             round(vL, 4), round(vR, 4), vbat])

                sleep = dt_nom - (time.monotonic() - loop_t0)
                if sleep > 0:
                    time.sleep(sleep)
    except KeyboardInterrupt:
        print("\n[i] Przerwano — zatrzymuję.")
    finally:
        send(ser, {"T": 11, "L": 0, "R": 0})
        send(ser, {"T": 1, "L": 0.0, "R": 0.0})
        send(ser, {"T": 131, "cmd": 0})
        ser.flush()
        time.sleep(0.3)
        ser.close()

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "cmd", "vL", "vR", "vbat"])
        w.writerows(rows)

    if periods[1:]:
        import statistics as st
        p = periods[1:]
        print(f"[OK] {len(rows)} próbek -> {args.out}")
        print(f"[i] Okres pętli: śr {st.mean(p)*1e3:.1f} ms, "
              f"max {max(p)*1e3:.1f} ms, odch.std {st.pstdev(p)*1e3:.2f} ms "
              f"(nominalnie {dt_nom*1e3:.0f} ms) — do raportu (opóźnienie/jitter).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
