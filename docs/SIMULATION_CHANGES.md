# SNIFF — Środowisko symulacyjne (Gazebo + RViz2)

Dokumentacja zmian wprowadzonych względem czystego, sklonowanego repo (branch `vision_new`) w ramach budowy środowiska symulacyjnego do testów bez dostępu do fizycznego robota.

---

## TL;DR

- Zbudowano kompletne środowisko symulacyjne robota SNIFF: **Gazebo Classic 11 + RViz2**, oparte o już istniejący `robot_description` (bazowy model 6-kołowy + LiDAR + launch pipeline w `platform_control`).
- Dodano model **kamery głębi OAK-D Lite** (link + Gazebo depth camera plugin) do `robot.urdf.xacro`.
- Dodano testowy świat Gazebo (`sniff_test_world.world`) z 10 pachołkami + 3 puszkami jako przeszkodami do testów SLAM/detekcji.
- Rozszerzono `simulation.launch.py` o wczytywanie własnego świata i zapisanej konfiguracji RViz.
- Zaktualizowano `setup.py` pakietu `robot_description`, żeby instalował nowe katalogi (`worlds/`, `rviz_conf/`).
- **Uruchomienie:** `ros2 launch platform_control simulation.launch.py`
- ⚠️ **Znany problem:** `oak_detector_node.py` (branch `vision_new`) korzysta z DepthAI SDK bezpośrednio z hardware'em i **nie zadziała** na symulowanej kamerze — do testowania detekcji YOLO w symulacji potrzebny byłby osobny node na standardowych topikach ROS (niezaimplementowane, patrz sekcja TODO).

---

## Zmienione / nowe pliki

### `robot_description/urdf/robot.urdf.xacro` — zmodyfikowany

Dodano na końcu pliku (przed `</robot>`) sekcję kamery głębi OAK-D Lite:

- `camera_link` — bryła reprezentująca kamerę (91×28×18mm), zamontowana na przedniej, górnej krawędzi kadłuba
- `camera_link_optical` — dodatkowa "optyczna" ramka TF (konwencja ROS: oś Z do przodu), wymagana żeby obraz i chmura punktów miały poprawną orientację
- Gazebo `<sensor type="depth">` z pluginem `libgazebo_ros_camera.so`, publikujący obraz RGB, głębię i chmurę punktów w namespace `/sniff`

Parametry dostrojone podczas testów (odbiegają od pierwotnej propozycji):

| Parametr | Wartość | Powód |
|---|---|---|
| `<format>` | `B8G8R8` (zamiast `R8G8B8`) | Zgodność z konwencją OpenCV / `cv_bridge` (`bgr8`) — inaczej kanały czerwony i niebieski byłyby zamienione miejscami |
| `<max_depth>` | `50.0` (zamiast proponowanych `10.0`) | Przy 10m znaczna część kadru (odległa podłoga w polu widzenia kamery) wypadała poza zasięgiem sensora i renderowała się jako czerń w podglądzie |

⚠️ `max_depth=50.0` jest nierealistycznie wysoki względem specyfikacji prawdziwego OAK-D Lite (~12m efektywnego zasięgu głębi) — działa, ale nie do końca odzwierciedla rzeczywisty sprzęt. Do rozważenia przycięcie bliżej realnej wartości, jeśli zacznie przeszkadzać w testach ilościowych.

### `robot_description/setup.py` — zmodyfikowany

Dodano dwie linie do `data_files`, żeby `colcon build` instalował nowe katalogi do `install/share/robot_description/`:

```python
(os.path.join('share', package_name, 'rviz_conf'), glob('rviz_conf/*.rviz')),
(os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
```

(wcześniej instalowany był tylko `urdf/`)

### `robot_description/worlds/sniff_test_world.world` — nowy plik

Świat Gazebo zapisany z poziomu GUI (**File → Save World As**), zawierający 10 pachołków drogowych i 3 puszki jako statyczne przeszkody testowe do SLAM-u i (docelowo) detekcji kamerą. Plik generowany automatycznie przez Gazebo (format SDF) — nieedytowany ręcznie, nie ma potrzeby go czytać/edytować w edytorze tekstowym.

### `robot_description/rviz_conf/config_rviz2.rviz` — zmodyfikowany

Zapisana konfiguracja RViz2 (**File → Save Config As**), żeby przy starcie od razu wyświetlał sensowny widok bez ręcznej konfiguracji za każdym razem. Kluczowe zawartości:

- `RobotModel` z **`Description Topic` ustawionym na `/robot_description`** — to był kluczowy fix; bez tego pole zostawało puste i robot się w ogóle nie renderował w scenie (mimo że dane docierały poprawnie)
- `LaserScan` na `/scan`
- `Map` na `/map` (+ `/map_updates`)
- `TF` — wszystkie ramki, w tym nowe `camera_link` / `camera_link_optical`
- `Image` na `/sniff/oak_d_lite_depth/depth/image_raw`
- `PointCloud2` na `/sniff/oak_d_lite_depth/points`

⚠️ **Do ogarnięcia później — niespójne nazewnictwo topików kamery głębi:** rzeczywiste nazwy topików obrazu głębi (`/sniff/oak_d_lite_depth/depth/image_raw`, `/sniff/oak_d_lite_depth/points`) różnią się od zakładanych w `<remapping>` w xacro (`/sniff/camera/depth/...`). Plugin `libgazebo_ros_camera.so` dla wyjść specyficznych dla głębi (`depth/image_raw`, `points`) domyślnie prefiksuje je **nazwą sensora** (`oak_d_lite_depth`) niezależnie od zdefiniowanych remappingów — remapping zadziałał tylko dla standardowych wyjść `image_raw`/`camera_info` (obraz kolorowy). Nie blokuje to działania, ale nazewnictwo jest niespójne. Ujednolicenie: dodać `<camera_name>camera</camera_name>` w bloku pluginu w xacro.

### `platform_control/launch/simulation.launch.py` — zmodyfikowany

Trzy zmiany względem wersji bazowej:

1. **Własny świat zamiast pustego** — dodano `world_file` i przekazanie go jako `launch_argument` do `gazebo.launch.py`
2. **Poprawka typu parametru** — `robot_description` opakowano w `ParameterValue(..., value_type=str)`; bez tego `Command(['xacro ', xacro_file])` nie był poprawnie interpretowany jako string przez `robot_state_publisher`
3. **Własna konfiguracja RViz** — dodano `arguments=['-d', rviz_config_file]` do node'a `rviz2`, wskazujące na zapisany `config_rviz2.rviz`

---

## Jak uruchomić (dla kogoś, kto klonuje repo od zera)

```bash
cd ~/sniff_robot/ros2_ws
colcon build --packages-select robot_description platform_control --symlink-install
source install/setup.bash
ros2 launch platform_control simulation.launch.py
```

Powinno otworzyć się Gazebo (świat z pachołkami/puszkami) i RViz2 (gotowy widok: robot, LiDAR, mapa).

Test ruchu robotem:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## Znane problemy / TODO

1. **Detekcja YOLO nie działa w symulacji.** `sniff_vision/oak_detector_node.py` łączy się z kamerą przez DepthAI SDK bezpośrednio do hardware'u OAK-D Lite — SDK nie obsługuje urządzeń symulowanych. Do testowania detekcji w Gazebo potrzebny byłby osobny node subskrybujący `sensor_msgs/Image` (np. przez `ultralytics`/OpenCV + `cv_bridge`) — niezaimplementowane.
2. **Niespójne nazewnictwo topików kamery głębi** — patrz sekcja `config_rviz2.rviz` wyżej.
3. **`max_depth=50.0`** w symulowanej kamerze jest nierealistycznie wysoki względem specyfikacji OAK-D Lite (~12m).
4. Ważne znalezisko przy okazji — sekcja o niespójnym nazewnictwie topików kamery głębi (/sniff/oak_d_lite_depth/... zamiast /sniff/camera/depth/...) to coś, czego wcześniej nie zauważyłem w naszych rozmowach — remapping w xacro częściowo nie zadziałał tak jak zakładałem. Nie psuje to niczego teraz, ale warto to wiedzieć zanim ktoś będzie pisał node subskrybujący te topiki.
