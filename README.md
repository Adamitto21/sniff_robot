# SNIFF

Lista przydatnych komend

## Symulacja

```bash
ros2 launch platform_control simulation.launch.py 
```

## Strona internetowa
**⚠️ Uwaga:** wszystkie urządzenia muszą znajdować się w tej samej sieci.

```bash
# a) W kontenerze:
    ros2 launch sniff_bringup web_bringup.launch.py

# b) Serwowanie strony z hosta:
    cd apps/web_dashboard
    python3 -m http.server 8000

# c) w przeglądarce:
    http://<IP_HOSTA>:8000
```

`hostname -I`, by uzyskać IP hosta.

## sniff_bringup

```bash
ros2 launch sniff_bringup <plik.launch>
```

| plik.launch | Opis |
|---|--- 
| full_bringup.launch.py | uruchomić wszystkie node'y |
| lidar_bringup.launch.py | uruchomić lidara |
| camera_bringup.launch.py | uruchomić kamerę |
| web_bringup.launch.py | uruchomić stronę internetową |
