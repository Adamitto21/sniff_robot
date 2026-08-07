#!/usr/bin/env bash
# SNIFF — zbieranie danych do sprawozdania SysRA.
# Uruchom na HOŚCIE (Jetson): bash zbierz_dane.sh
# Wynik: sysra_dane.txt (wszystkie sekcje podpisane — wklejasz w [DO UZUPEŁNIENIA]).
# Wymaga działającego kontenera sniff_ros2 z uruchomionym stackiem (lidar itd.);
# sekcje ROS2 po prostu wyjdą puste, jeśli nody nie działają.

set -u
OUT="sysra_dane.txt"
C="docker exec sniff_ros2 bash -lc"
SRC="source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash 2>/dev/null"

sec() { echo -e "\n============================================================\n### $1\n============================================================" >> "$OUT"; }

echo "SNIFF — dane do sprawozdania SysRA — $(date)" > "$OUT"

# ---------- HOST: warstwa fizyczna ----------
sec "3. lsusb (urządzenia USB)"
lsusb >> "$OUT" 2>&1

sec "3. Porty szeregowe (ls -la /dev/tty{USB,ACM,CH343,THS}*)"
ls -la /dev/ttyUSB* /dev/ttyACM* /dev/ttyCH343* /dev/ttyTHS* >> "$OUT" 2>&1

sec "3. Identyfikacja konwerterów (udevadm: producent/model per port)"
for d in /dev/ttyUSB0 /dev/ttyACM0 /dev/ttyCH343USB0; do
  [ -e "$d" ] || continue
  echo "--- $d ---" >> "$OUT"
  udevadm info -q property -n "$d" 2>/dev/null | \
    grep -E "ID_VENDOR=|ID_MODEL=|ID_USB_DRIVER=|DEVNAME=" >> "$OUT"
done

sec "3. Magistrala I2C — skan (SCD40 powinien być pod 0x62)"
if command -v i2cdetect >/dev/null; then
  for bus in 1 7; do
    echo "--- i2cdetect -y $bus ---" >> "$OUT"
    sudo i2cdetect -y "$bus" >> "$OUT" 2>&1
  done
else
  echo "(brak i2cdetect: sudo apt install i2c-tools)" >> "$OUT"
fi

sec "7. dmesg — zdarzenia USB/tty z bieżącego rozruchu (rozłączenia, enumeracja)"
sudo dmesg --time-format iso 2>/dev/null | \
  grep -iE "usb|tty|ch34|cp210|disconnect" | tail -n 80 >> "$OUT"

sec "6. docker-compose.yml — sekcje devices/volumes/environment"
CANDIDATES="$HOME/r/sniff_robot/docker-compose.yml $HOME/r/sniff_robot/docker/jetson/docker-compose.yml"
for f in $CANDIDATES; do
  if [ -f "$f" ]; then echo "--- $f ---" >> "$OUT"; cat "$f" >> "$OUT"; fi
done

# ---------- KONTENER: warstwa aplikacji (ROS2/DDS) ----------
sec "5.1 ros2 node list"
$C "$SRC && timeout 15 ros2 node list" >> "$OUT" 2>&1

sec "5.1 ros2 topic list -t (topiki + typy)"
$C "$SRC && timeout 15 ros2 topic list -t" >> "$OUT" 2>&1

sec "5.2 QoS kluczowych topików (ros2 topic info --verbose)"
for t in /scan /cmd_vel /map /detections /sniff/camera/image; do
  echo "--- $t ---" >> "$OUT"
  $C "$SRC && timeout 15 ros2 topic info $t --verbose" >> "$OUT" 2>&1
done

sec "5.1/7.1 Częstotliwości publikacji (10 s pomiaru na topik)"
for t in /scan /sniff/camera/image; do
  echo "--- ros2 topic hz $t ---" >> "$OUT"
  $C "$SRC && timeout 12 ros2 topic hz $t --window 50" >> "$OUT" 2>&1
done

sec "5.3 Implementacja DDS (RMW) używana przez ROS2"
$C "$SRC && echo RMW=\$RMW_IMPLEMENTATION && ros2 doctor --report 2>/dev/null | grep -iA2 'middleware'" >> "$OUT" 2>&1

# ---------- 4.3: pomiar częstotliwości strumienia stanu ESP32 ----------
sec "4.3 Strumień stanu ESP32 (T=1001) — pomiar liczby ramek/s"
echo "UWAGA: wymaga wolnego portu (zatrzymaj platform_driver)." >> "$OUT"
echo "UWAGA: otwarcie portu RESETUJE ESP32 — nie uruchamiaj w trakcie jazdy robota." >> "$OUT"
python3 - >> "$OUT" 2>&1 <<'PYEOF'
import json, time
try:
    import serial
except ImportError:
    print("(pominięto: brak pyserial na hoście — pip3 install pyserial)"); raise SystemExit
try:
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = '/dev/ttyCH343USB0', 115200, 0.1
    s.dtr = False; s.rts = False; s.exclusive = True
    s.open()
except Exception as e:
    print(f"(pominięto: port zajęty lub brak — {e})"); raise SystemExit
time.sleep(2.5); s.reset_input_buffer()   # ESP32 resetuje się przy otwarciu portu
s.write(b'{"T":143,"cmd":0}\n'); s.write(b'{"T":142,"cmd":0}\n'); s.write(b'{"T":131,"cmd":1}\n')
time.sleep(0.3); s.reset_input_buffer()
n, t0 = 0, time.monotonic()
while time.monotonic() - t0 < 5.0:
    line = s.readline()
    if not line: continue
    try:
        if json.loads(line.decode(errors="ignore")).get("T") == 1001: n += 1
    except Exception: pass
s.write(b'{"T":131,"cmd":0}\n'); s.close()
print(f"Ramki T=1001: {n} w 5.0 s -> {n/5.0:.1f} Hz (przy odstępie dodatkowym 0 ms)")
PYEOF

echo -e "\n[OK] Wszystko zapisane do: $OUT"
echo "Wklej odpowiednie sekcje w miejsca [DO UZUPEŁNIENIA] w SYSRA_RAPORT_SZKIELET.md"
