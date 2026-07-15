# sniff_robot — panel webowy (kokpit)

Lokalna strona do sterowania robotem i podglądu danych na żywo: joystick + klawiatura,
obraz z kamery OAK-D, mapa ze SLAM z pozycją robota i nakładką skanu lidara,
karty czujników (np. jakości powietrza) oraz przeglądarka topików ROS2.

Działa na laptopie i telefonie w tej samej sieci co robot. **Zero zależności** —
strona nie korzysta z CDN ani bibliotek, więc działa w sieci robota bez internetu.

## Architektura

```
przeglądarka (laptop / telefon)
   │  ws://JETSON:9090  ─────────►  rosbridge_websocket ──► topiki ROS2
   │  http://JETSON:8080/stream ─►  web_video_server    ──► obraz z kamery (MJPEG)
   └  http://JETSON:8000        ─►  python3 -m http.server (te pliki)
```

> Gdyby ros-humble-web-video-server` nie było w repo dla architektury Jetsona,
> zbuduj go ze źródeł w workspace: `git clone -b ros2 https://github.com/RobotWebTools/web_video_server`
> do `src/` i `colcon build`.

## Porty w Dockerze

Jeśli kontener działa z `network_mode: host` — **nic nie robisz**.
Jeśli nie, dodaj w `docker-compose.yml`:

```yaml
    ports:
      - "9090:9090"   # rosbridge
      - "8080:8080"   # web_video_server
```

## Uruchomienie

```bash
# a) backend w kontenerze:
ros2 launch sniff_bringup web_bringup.launch.py

# b) serwowanie strony z hosta (Jetson):
cd ~/r/sniff_robot/apps/web_dashboard
python3 -m http.server 8000

# c) w przeglądarce:
#    http://<IP_JETSONA>:8000
```

`hostname -I`, by uzyskać IP Jetsona.

## Pierwsze kroki na stronie

1. **Zielona kropka** w nagłówku = połączono z rosbridge.
2. **Topic sterowania**: kliknij **📋 Topiki** → wiersze typu `Twist` są podświetlone →
   przy właściwym kliknij **→ sterowanie**. (Domyślnie ustawiony jest `/cmd_vel`.)
   Nie wiesz który? Kliknij **podgląd** i rusz robotem oryginalnym sposobem — zobaczysz,
   gdzie lecą komendy.
3. **Kamera**: jeśli czarny ekran — otwórz `http://<IP>:8080` (link jest w nakładce
   błędu); web_video_server wyświetla tam listę dostępnych topików obrazu.
   Właściwy ustawisz w **📋 Topiki** przyciskiem **→ kamera** albo w ⚙.
4. **Mapa**: pojawi się po uruchomieniu SLAM (`lidar_bringup.launch.py`).
   Kółko myszy / pinch = zoom, przeciąganie = przesuwanie, **⤢** = dopasuj,
   **skan** = nakładka punktów lidara.
5. **Czujniki**: gdy node czujnika (np. jakości powietrza) zacznie publikować,
   kliknij **+ dodaj** → przy topiku **+ czujnik** → podaj nazwę i jednostkę.
   Karta z wartością i mini-wykresem pojawi się od razu i zostanie zapamiętana.

## Sterowanie i bezpieczeństwo

- Joystick (dotyk/mysz) oraz klawiatura: `W A S D` / strzałki, `spacja` = STOP.
- Suwaki ograniczają maksymalną prędkość liniową i obrotową.
- Komenda publikowana jest 10 Hz tylko podczas sterowania; po puszczeniu
  wysyłana jest seria zer (zatrzymanie).
- STOP wysyłany jest też automatycznie przy schowaniu karty przeglądarki
  i utracie połączenia. Na telefonie masz stały pływający przycisk STOP.

## Najczęstsze problemy

| Objaw | Przyczyna / rozwiązanie |
|---|---|
| Czerwona kropka "brak połączenia" | rosbridge nie działa albo port 9090 niewystawiony z kontenera |
| Strona działa na laptopie, na telefonie nie | telefon w innej sieci Wi-Fi, albo firewall na hoście |
| Czarna kamera | zły topic — sprawdź listę na `http://<IP>:8080`; czy `camera_bringup` działa? |
| Brak mapy | SLAM nie uruchomiony, albo inny topic niż `/map` (zmień w ⚙) |
| Robot nie jedzie, komendy "lecą" | zły topic Twist — znajdź właściwy w 📋 i kliknij **→ sterowanie** |
| Robot bez pozycji na mapie | slam_toolbox publikuje pozę na `/pose` — jeśli u Ciebie inaczej, zmień w ⚙ |

Konfiguracja (host, topiki, prędkości, czujniki) zapisuje się w przeglądarce
(localStorage) — **przywróć domyślne** w ⚙ czyści wszystko.
