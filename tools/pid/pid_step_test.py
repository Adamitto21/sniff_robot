#!/usr/bin/env python3
"""
SNIFF — test odpowiedzi skokowej kół UGV02 (firmware ugv_base_general).

Wysyła skok PWM (identyfikacja, otwarta pętla) albo skok prędkości (pętla zamknięta),
loguje feedback {"T":1001,...} (prędkości kół z enkoderów) do CSV.

Przykłady:
  identyfikacja:  python3 pid_step_test.py --mode pwm   --amp0 80  --t0 3 --amp1 150 --t1 4 --out ident.csv
  pętla zamknięta: python3 pid_step_test.py --mode speed --pid 20 2000 0 255 \
                       --amp0 0.15 --t0 3 --amp1 0.35 --t1 4 --out krok.csv

CSV: t[s], cmd (PWM albo m/s), vL[m/s], vR[m/s], vbat[V]
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
READY_TIMEOUT_S = 25.0  # boot z WiFi AP + misją boot potrafi trwać kilkanaście sekund


def open_serial(port: str, baud: int, timeout: float = 0.05) -> serial.Serial:
    """Otwiera port z opuszczonymi DTR/RTS (minimalizuje reset ESP32) i czeka na boot."""
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = timeout
    ser.dtr = False
    ser.rts = False
    ser.exclusive = True          # nie pozwól drugiemu procesowi otworzyć portu
    ser.open()
    print(f"[i] Port otwarty, czekam {BOOT_WAIT_S:.1f} s na start ESP32...")
    time.sleep(BOOT_WAIT_S)
    ser.reset_input_buffer()
    return ser


def wait_ready(ser: serial.Serial, interval_ms: int) -> bool:
    """Odpytuje płytkę aż odpowie ramką T:1001. Odporne na długi boot (WiFi AP,
    misja boot) — komendy wysłane w trakcie setup() przepadają, więc ponawiamy."""
    print("[i] Czekam na gotowość ESP32 (odpytywanie {\"T\":130})...")
    t0 = time.monotonic()
    while time.monotonic() - t0 < READY_TIMEOUT_S:
        send(ser, {"T": 143, "cmd": 0})              # echo off
        send(ser, {"T": 142, "cmd": interval_ms})    # odstęp feedbacku
        send(ser, {"T": 131, "cmd": 1})              # strumień feedbacku ON
        send(ser, {"T": 130})                        # pojedyncza ramka na próbę
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if parse_line(ser.readline()) is not None:
                print(f"[i] ESP32 gotowy po {time.monotonic() - t0:.1f} s.")
                ser.reset_input_buffer()
                return True
    print(f"[!] Brak odpowiedzi przez {READY_TIMEOUT_S:.0f} s.")
    return False


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


def cmd_for(mode: str, amp: float) -> dict:
    if mode == "pwm":
        return {"T": 11, "L": int(amp), "R": int(amp)}
    return {"T": 1, "L": float(amp), "R": float(amp)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", default="/dev/ttyCH343USB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--mode", choices=["pwm", "speed"], required=True,
                    help="pwm: {'T':11} otwarta pętla; speed: {'T':1} zadana prędkość [m/s]")
    ap.add_argument("--amp0", type=float, default=0.0, help="wartość przed skokiem")
    ap.add_argument("--t0", type=float, default=2.0, help="czas przed skokiem [s]")
    ap.add_argument("--amp1", type=float, required=True, help="wartość po skoku")
    ap.add_argument("--t1", type=float, default=4.0, help="czas po skoku [s]")
    ap.add_argument("--pid", nargs=4, type=float, metavar=("P", "I", "D", "L"),
                    help="ustaw nastawy PID przed testem, np. --pid 20 2000 0 255")
    ap.add_argument("--pid-mid", nargs=4, type=float, metavar=("P", "I", "D", "L"),
                    help="KROK 0: podmień nastawy PID w trakcie 2. fazy (bez 2. procesu). "
                         "Jeśli prędkość się nie zmieni -> pętla OTWARTA.")
    ap.add_argument("--interval", type=int, default=20,
                    help="odstęp feedbacku [ms] ({'T':142})")
    ap.add_argument("--out", default="step.csv")
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)

    rows = []
    try:
        if not wait_ready(ser, args.interval):
            print("[!] ESP32 nie odpowiada. Sprawdź:\n"
                  "    - czy port jest wolny (platform_driver / arduino-cli monitor?)\n"
                  "    - czy to właściwy /dev/tty* (arduino-cli board list)\n"
                  "    - podejrzyj boot: arduino-cli monitor -p <port> -c baudrate=115200")
            return 1
        if args.pid:
            p, i, d, l = args.pid
            send(ser, {"T": 2, "P": p, "I": i, "D": d, "L": l})
            print(f"[i] Nastawy PID: P={p} I={i} D={d} L={l}")
        time.sleep(0.3)
        ser.reset_input_buffer()

        t_start = time.monotonic()
        phase_plan = [(args.amp0, args.t0), (args.amp1, args.t1)]
        print(f"[i] Start: {args.mode}, {args.amp0} przez {args.t0}s -> "
              f"{args.amp1} przez {args.t1}s")

        for phase_idx, (amp, dur) in enumerate(phase_plan):
            send(ser, cmd_for(args.mode, amp))
            phase_start = time.monotonic()
            last_keepalive = phase_start
            mid_done = False
            while time.monotonic() - phase_start < dur:
                now = time.monotonic()
                # KROK 0: podmiana nastaw w połowie drugiej fazy
                if (args.pid_mid and phase_idx == 1 and not mid_done
                        and now - phase_start > dur / 2.0):
                    p, i, d, l = args.pid_mid
                    send(ser, {"T": 2, "P": p, "I": i, "D": d, "L": l})
                    print(f"[i] t={now - t_start:.2f}s: podmiana PID -> "
                          f"P={p} I={i} D={d} L={l}")
                    mid_done = True
                if now - last_keepalive > KEEPALIVE_S:
                    send(ser, cmd_for(args.mode, amp))  # heartbeat
                    last_keepalive = now
                line = ser.readline()
                if not line:
                    continue
                fb = parse_line(line)
                if fb is None:
                    continue
                rows.append([round(now - t_start, 4), amp,
                             fb.get("L"), fb.get("R"), fb.get("v")])
    finally:
        # bezpieczne zatrzymanie niezależnie od trybu
        # (UWAGA: {"T":0} NIE istnieje w tym firmware — nie jest to stop!)
        send(ser, {"T": 1, "L": 0.0, "R": 0.0})
        send(ser, {"T": 11, "L": 0, "R": 0})
        send(ser, {"T": 131, "cmd": 0})
        ser.flush()          # wypchnij bufor zanim zamkniemy port
        time.sleep(0.3)      # daj ESP32 czas na odebranie i wykonanie
        ser.close()

    if not rows:
        print("[!] Brak ramek feedbacku (T:1001). Sprawdź, czy port jest wolny "
              "(platform_driver wyłączony?) i czy to właściwy /dev/tty*.")
        return 1

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "cmd", "vL", "vR", "vbat"])
        w.writerows(rows)
    dt = (rows[-1][0] - rows[0][0]) / max(len(rows) - 1, 1)
    print(f"[OK] {len(rows)} próbek -> {args.out} (śr. okres {dt*1000:.1f} ms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
