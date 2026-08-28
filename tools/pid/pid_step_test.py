#!/usr/bin/env python3
"""
SNIFF — test odpowiedzi skokowej kół UGV02 (firmware ugv_base_general).

Wersja 2: CSV zawiera dodatkowo liczniki odometrii odl/odr z ramki T:1001.
Prędkość w polach L/R jest skwantowana co 0.381 m/s (jeden impuls na cykl pętli
firmware) i nie nadaje się do identyfikacji. Liczniki odl/odr rosną monotonicznie,
więc prędkość odtwarza się z nich przez różniczkowanie po oknie, z rozdzielczością
lepszą o dwa rzędy wielkości. Robi to pid_identify2.py.

Przykłady:
  identyfikacja:   python3 pid_step_test.py --mode pwm --amp0 60 --t0 1.5 --amp1 255 --t1 1.5 --out ident_1.csv
  pętla zamknięta: python3 pid_step_test.py --mode speed --pid 20 2000 0 255 \
                       --amp0 0.30 --t0 3 --amp1 0.60 --t1 5 --out krok.csv

CSV: t[s], cmd (PWM albo m/s), vL[m/s], vR[m/s], odl, odr, vbat
UWAGA: zatrzymaj platform_driver przed uruchomieniem (port może otworzyć tylko 1 proces).
"""
import argparse
import csv
import json
import sys
import time

import serial

KEEPALIVE_S = 0.8  # heartbeat firmware = 3 s
BOOT_WAIT_S = 3.0  # ESP32 resetuje się przy otwarciu portu (DTR/RTS)
READY_TIMEOUT_S = 25.0


def open_serial(port: str, baud: int, timeout: float = 0.05) -> serial.Serial:
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


def send(ser: serial.Serial, obj: dict) -> None:
    ser.write((json.dumps(obj) + "\n").encode())


def parse_line(line: bytes):
    try:
        d = json.loads(line.decode(errors="ignore").strip())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if isinstance(d, dict) and d.get("T") == 1001:
        return d
    return None


def wait_ready(ser: serial.Serial, interval_ms: int) -> bool:
    print("[i] Czekam na gotowość ESP32 (odpytywanie {\"T\":130})...")
    t0 = time.monotonic()
    while time.monotonic() - t0 < READY_TIMEOUT_S:
        send(ser, {"T": 143, "cmd": 0})              # echo off
        send(ser, {"T": 142, "cmd": interval_ms})    # odstęp feedbacku
        send(ser, {"T": 131, "cmd": 1})              # strumień feedbacku ON
        send(ser, {"T": 130})
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if parse_line(ser.readline()) is not None:
                print(f"[i] ESP32 gotowy po {time.monotonic() - t0:.1f} s.")
                ser.reset_input_buffer()
                return True
    print(f"[!] Brak odpowiedzi przez {READY_TIMEOUT_S:.0f} s.")
    return False


def cmd_for(mode: str, amp: float) -> dict:
    if mode == "pwm":
        return {"T": 11, "L": int(amp), "R": int(amp)}
    return {"T": 1, "L": float(amp), "R": float(amp)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", default="/dev/ttyCH343USB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--mode", choices=["pwm", "speed"], required=True)
    ap.add_argument("--amp0", type=float, default=0.0, help="wartość przed skokiem")
    ap.add_argument("--t0", type=float, default=2.0, help="czas przed skokiem [s]")
    ap.add_argument("--amp1", type=float, required=True, help="wartość po skoku")
    ap.add_argument("--t1", type=float, default=4.0, help="czas po skoku [s]")
    ap.add_argument("--pid", nargs=4, type=float, metavar=("P", "I", "D", "L"),
                    help="ustaw nastawy PID przed testem, np. --pid 20 2000 0 255")
    ap.add_argument("--pid-mid", nargs=4, type=float, metavar=("P", "I", "D", "L"),
                    help="KROK 0: podmień nastawy w trakcie 2. fazy")
    ap.add_argument("--interval", type=int, default=20,
                    help="odstęp feedbacku [ms] ({'T':142})")
    ap.add_argument("--rampa", type=float, default=0.8,
                    help="czas łagodnego wyhamowania na końcu [s]. 0 wyłącza. "
                         "Nagłe zerowanie PWM hamuje dynamicznie i przechyla robota.")
    ap.add_argument("--out", default="step.csv")
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)

    rows = []
    try:
        if not wait_ready(ser, args.interval):
            print("[!] Sprawdź: platform_driver zatrzymany? właściwy /dev/tty*?")
            return 1
        if args.pid:
            p, i, d, l = args.pid
            send(ser, {"T": 2, "P": p, "I": i, "D": d, "L": l})
            print(f"[i] Nastawy PID: P={p} I={i} D={d} L={l}")
        time.sleep(0.3)
        ser.reset_input_buffer()

        t_start = time.monotonic()
        print(f"[i] Start: {args.mode}, {args.amp0} przez {args.t0}s -> "
              f"{args.amp1} przez {args.t1}s")

        for phase_idx, (amp, dur) in enumerate([(args.amp0, args.t0),
                                                (args.amp1, args.t1)]):
            send(ser, cmd_for(args.mode, amp))
            phase_start = time.monotonic()
            last_keepalive = phase_start
            mid_done = False
            while time.monotonic() - phase_start < dur:
                now = time.monotonic()
                if (args.pid_mid and phase_idx == 1 and not mid_done
                        and now - phase_start > dur / 2.0):
                    p, i, d, l = args.pid_mid
                    send(ser, {"T": 2, "P": p, "I": i, "D": d, "L": l})
                    print(f"[i] t={now - t_start:.2f}s: podmiana PID -> "
                          f"P={p} I={i} D={d} L={l}")
                    mid_done = True
                if now - last_keepalive > KEEPALIVE_S:
                    send(ser, cmd_for(args.mode, amp))
                    last_keepalive = now
                line = ser.readline()
                if not line:
                    continue
                fb = parse_line(line)
                if fb is None:
                    continue
                rows.append([round(now - t_start, 4), amp,
                             fb.get("L"), fb.get("R"),
                             fb.get("odl"), fb.get("odr"), fb.get("v")])
        # łagodne wyhamowanie zamiast nagłego zerowania sterowania
        if args.rampa > 0:
            print(f"[i] Hamowanie po rampie {args.rampa:.1f} s...")
            krokow = max(int(args.rampa / 0.05), 1)
            for j in range(krokow, 0, -1):
                send(ser, cmd_for(args.mode, args.amp1 * j / krokow))
                time.sleep(args.rampa / krokow)
    finally:
        send(ser, {"T": 1, "L": 0.0, "R": 0.0})
        send(ser, {"T": 11, "L": 0, "R": 0})
        send(ser, {"T": 131, "cmd": 0})
        ser.flush()
        time.sleep(0.3)
        ser.close()

    if not rows:
        print("[!] Brak ramek feedbacku (T:1001). Port zajęty?")
        return 1

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "cmd", "vL", "vR", "odl", "odr", "vbat"])
        w.writerows(rows)

    dt = (rows[-1][0] - rows[0][0]) / max(len(rows) - 1, 1)
    print(f"[OK] {len(rows)} próbek -> {args.out} (śr. okres {dt*1000:.1f} ms)")

    # kontrola: czy liczniki odometrii w ogóle się ruszyły
    try:
        o0, o1 = rows[0][4], rows[-1][4]
        if o0 is None or o1 is None:
            print("[!] Brak pól odl/odr w ramce — identyfikacja będzie na "
                  "skwantowanym vL/vR.")
        elif abs(float(o1) - float(o0)) < 1e-9:
            print("[!] Licznik odl nie drgnął. Koło się nie kręciło albo "
                  "firmware nie aktualizuje odometrii.")
        else:
            print(f"[i] Przyrost odl: {float(o1) - float(o0):.4f}, "
                  f"odr: {float(rows[-1][5]) - float(rows[0][5]):.4f}")
    except (TypeError, ValueError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
