#!/usr/bin/env python3
"""
SNIFF — interaktywna konsola komend UGV02 (firmware ugv_base_general).

Wpisujesz ramkę JSON, Enter -> leci do ESP32. W tle wątek podtrzymuje ostatnią
komendę ruchu (watchdog firmware = 3 s) i pokazuje feedback z enkoderów.

Uruchomienie:
    python3 ugv_console.py                       # domyślnie /dev/ttyCH343USB0
    python3 ugv_console.py --port /dev/ttyUSB0
    python3 ugv_console.py --no-keepalive        # bez podtrzymywania (robot stanie po 3 s)

Skróty (zamiast pisania JSON-a):
    0.3 0.3      -> {"T":1,"L":0.3,"R":0.3}      (prędkości kół m/s)
    s / stop     -> zatrzymanie
    fb on / off  -> strumień feedbacku
    pid P I D L  -> {"T":2,...}
    ?            -> ściąga komend
    q            -> wyjście (ze stopem)
"""
import argparse
import json
import sys
import threading
import time

import serial

BOOT_WAIT_S = 4.0
KEEPALIVE_S = 0.8

HELP = """
Najczęstsze ramki:
  {"T":1,"L":0.3,"R":0.3}          prędkości kół [m/s], zakres +-2.0
  {"T":11,"L":120,"R":120}         bezpośrednie PWM +-255 (wyłącza regulator)
  {"T":2,"P":20,"I":2000,"D":0,"L":255}   nastawy PID (+ limit antywindup)
  {"T":130}                        pojedyncza ramka stanu
  {"T":131,"cmd":1}                strumień stanu ON  (0 = OFF)
  {"T":142,"cmd":20}               okres strumienia stanu [ms]
  {"T":143,"cmd":0}                echo komend OFF
Odpowiedź T=1001: L/R = prędkości kół [m/s], r/p/y = IMU, v = napięcie [V]
UWAGA: {"T":0} NIE istnieje w tym firmware (ramka jest ignorowana).
"""


def open_serial(port, baud):
    ser = serial.Serial()
    ser.port, ser.baudrate, ser.timeout = port, baud, 0.1
    ser.dtr = False
    ser.rts = False
    ser.exclusive = True
    ser.open()
    print(f"[i] {port} @ {baud} — czekam {BOOT_WAIT_S} s na start ESP32 "
          f"(otwarcie portu resetuje płytkę)...")
    time.sleep(BOOT_WAIT_S)
    ser.reset_input_buffer()
    return ser


class Console:
    def __init__(self, ser, keepalive=True):
        self.ser = ser
        self.keepalive = keepalive
        self.last_motion = None      # ostatnia komenda ruchu do podtrzymywania
        self.lock = threading.Lock()
        self.running = True
        self.show_fb = False

    def send(self, obj):
        with self.lock:
            self.ser.write((json.dumps(obj) + "\n").encode())
        if obj.get("T") in (1, 11, 13):
            self.last_motion = obj if any(
                abs(float(obj.get(k, 0))) > 0 for k in ("L", "R", "X", "Z")) else None

    def reader(self):
        while self.running:
            try:
                line = self.ser.readline()
            except Exception:
                break
            if not line:
                continue
            txt = line.decode(errors="ignore").strip()
            if not txt:
                continue
            try:
                d = json.loads(txt)
            except json.JSONDecodeError:
                print(f"\r  << {txt}\n> ", end="", flush=True)
                continue
            if d.get("T") == 1001:
                if self.show_fb:
                    print(f"\r  vL={d.get('L'):+.3f} vR={d.get('R'):+.3f} "
                          f"yaw={d.get('y')} bat={d.get('v')}V   \n> ",
                          end="", flush=True)
            else:
                print(f"\r  << {txt}\n> ", end="", flush=True)

    def heart(self):
        while self.running:
            time.sleep(KEEPALIVE_S)
            if self.keepalive and self.last_motion:
                with self.lock:
                    self.ser.write((json.dumps(self.last_motion) + "\n").encode())

    def stop(self):
        self.last_motion = None
        self.send({"T": 1, "L": 0.0, "R": 0.0})
        self.send({"T": 11, "L": 0, "R": 0})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", default="/dev/ttyCH343USB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--no-keepalive", action="store_true")
    args = ap.parse_args()

    try:
        ser = open_serial(args.port, args.baud)
    except Exception as e:
        print(f"[!] Nie mogę otworzyć portu: {e}")
        print("    Sprawdź: czy platform_driver jest zatrzymany? "
              "chmod 666 na porcie? właściwa nazwa /dev/tty*?")
        return 1

    c = Console(ser, keepalive=not args.no_keepalive)
    threading.Thread(target=c.reader, daemon=True).start()
    threading.Thread(target=c.heart, daemon=True).start()
    c.send({"T": 143, "cmd": 0})   # echo off — czytelniejsza konsola

    print(HELP if False else "[i] Gotowe. '?' = pomoc, 'q' = wyjście, 's' = stop.")
    try:
        while True:
            try:
                raw = input("> ").strip()
            except EOFError:
                break
            if not raw:
                continue
            low = raw.lower()

            if low in ("q", "quit", "exit"):
                break
            if low == "?":
                print(HELP); continue
            if low in ("s", "stop"):
                c.stop(); print("  [stop]"); continue
            if low.startswith("fb"):
                on = "off" not in low
                c.show_fb = on
                c.send({"T": 142, "cmd": 100})
                c.send({"T": 131, "cmd": 1 if on else 0})
                print(f"  [feedback {'ON' if on else 'OFF'}]"); continue
            if low.startswith("pid"):
                p = raw.split()[1:]
                if len(p) != 4:
                    print("  użycie: pid P I D L   np. pid 20 2000 0 255"); continue
                c.send({"T": 2, "P": float(p[0]), "I": float(p[1]),
                        "D": float(p[2]), "L": float(p[3])})
                print("  [nastawy wysłane]"); continue

            # "0.3 0.3" -> komenda prędkości
            parts = raw.split()
            if len(parts) == 2:
                try:
                    c.send({"T": 1, "L": float(parts[0]), "R": float(parts[1])})
                    print(f"  >> T:1 L={parts[0]} R={parts[1]}"); continue
                except ValueError:
                    pass

            # w przeciwnym razie: surowy JSON
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                print("  [!] To nie jest poprawny JSON ani skrót. '?' = pomoc.")
                continue
            c.send(obj)
            print(f"  >> {json.dumps(obj)}")
    except KeyboardInterrupt:
        pass
    finally:
        c.stop()
        time.sleep(0.2)
        c.running = False
        ser.close()
        print("\n[i] Zatrzymano, port zamknięty.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
