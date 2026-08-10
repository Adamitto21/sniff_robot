#!/usr/bin/env python3
"""
SNIFF — podgląd surowej ramki T:1001.

Sprawdza, jakie pola naprawdę wysyła firmware. Kluczowe pytanie: czy jest tam
licznik impulsów enkodera (odl/odr albo podobne). Jeśli tak, prędkość da się
policzyć z różnicy pozycji zamiast z kwantowanego pola L/R.

    python3 ramka_check.py
"""
import json
import sys
import time

import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyCH343USB0"

s = serial.Serial()
s.port, s.baudrate, s.timeout = PORT, 115200, 0.1
s.dtr = False
s.rts = False
s.exclusive = True
s.open()
print(f"[i] {PORT} — czekam 3 s na start ESP32...")
time.sleep(3.0)
s.reset_input_buffer()

s.write(b'{"T":143,"cmd":0}\n')
s.write(b'{"T":142,"cmd":50}\n')
s.write(b'{"T":131,"cmd":1}\n')
time.sleep(0.3)
s.reset_input_buffer()

print("[i] Ramki przez 3 s (surowo):\n")
pola = set()
n = 0
t0 = time.monotonic()
while time.monotonic() - t0 < 3.0:
    line = s.readline()
    if not line:
        continue
    txt = line.decode(errors="ignore").strip()
    try:
        d = json.loads(txt)
    except json.JSONDecodeError:
        continue
    if isinstance(d, dict) and d.get("T") == 1001:
        n += 1
        pola |= set(d.keys())
        if n <= 5:
            print("   ", txt)

s.write(b'{"T":131,"cmd":0}\n')
s.flush()
time.sleep(0.2)
s.close()

print(f"\n[i] Ramek: {n}")
print(f"[i] Pola w ramce: {sorted(pola)}")
liczniki = [p for p in pola if p.lower() in ("odl", "odr", "encl", "encr", "el", "er")]
if liczniki:
    print(f"[OK] Jest licznik impulsów: {liczniki} — można liczyć prędkość z pozycji.")
else:
    print("[!] Brak licznika impulsów w ramce — zostaje ścieżka z większym skokiem "
          "i uśrednianiem przebiegów.")
