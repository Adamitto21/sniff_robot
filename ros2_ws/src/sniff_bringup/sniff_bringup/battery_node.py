#!/usr/bin/env python3
"""
battery_node.py — stan zasilania UGV02 jako sensor_msgs/BatteryState

Po co: płytka UGV02 podaje napięcie w telemetrii po UART, ale surowa liczba
nie mówi wiele. Ten node przelicza ją na stan naładowania i publikuje
w standardowym typie, który rozumieją narzędzia ROS2 i panel webowy.

UWAGA — konflikt o port szeregowy:
  /dev/ttyTHS0 obsługuje tylko jeden program naraz. Jeśli działa node
  sterownika UGV, ten node nie otworzy portu. Wtedy użyj trybu --from-topic,
  w którym napięcie jest brane z topicu publikowanego przez sterownik,
  zamiast czytać port bezpośrednio.

Publikuje:
  /battery   sensor_msgs/BatteryState

Uruchomienie:
  ros2 run sniff_bringup battery_node
  ros2 run sniff_bringup battery_node --ros-args -p port:=/dev/ttyUSB0
  ros2 run sniff_bringup battery_node --ros-args -p from_topic:=/ugv/status \\
                                                 -p voltage_field:=voltage
"""

import json
import math
import threading

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState

# Krzywa rozładowania ogniwa Li-ion 18650: (napięcie na ogniwo, stan naładowania)
# Płaska w środku zakresu — dlatego procent z napięcia jest tylko przybliżeniem.
CELL_CURVE = [
    (4.20, 1.00), (4.10, 0.95), (4.00, 0.88), (3.90, 0.78), (3.80, 0.67),
    (3.70, 0.55), (3.60, 0.42), (3.50, 0.28), (3.40, 0.15), (3.30, 0.06),
    (3.20, 0.02), (3.00, 0.00),
]


def soc_from_voltage(v_total, cells):
    """Stan naładowania 0..1 z napięcia całej paczki."""
    if cells <= 0 or not math.isfinite(v_total):
        return float('nan')
    v = v_total / cells
    if v >= CELL_CURVE[0][0]:
        return 1.0
    if v <= CELL_CURVE[-1][0]:
        return 0.0
    for i in range(len(CELL_CURVE) - 1):
        v_hi, s_hi = CELL_CURVE[i]
        v_lo, s_lo = CELL_CURVE[i + 1]
        if v_lo <= v <= v_hi:
            # interpolacja liniowa między punktami krzywej
            t = (v - v_lo) / (v_hi - v_lo)
            return s_lo + t * (s_hi - s_lo)
    return float('nan')


class BatteryNode(Node):

    def __init__(self):
        super().__init__('battery_node')

        self.declare_parameter('port', '/dev/ttyCH343USB0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('cells', 3)              # UGV02: 3 ogniwa 18650
        self.declare_parameter('publish_topic', '/battery')
        self.declare_parameter('rate', 1.0)             # Hz
        self.declare_parameter('smooth', 0.3)           # 0..1, wygładzanie odczytu
        # tryb alternatywny: bierz napięcie z istniejącego topicu zamiast z portu
        self.declare_parameter('from_topic', '')
        self.declare_parameter('voltage_field', 'voltage')

        self.cells = self.get_parameter('cells').value
        self.alpha = float(self.get_parameter('smooth').value)
        self.voltage = float('nan')
        self.current = float('nan')
        self._lock = threading.Lock()

        topic = self.get_parameter('publish_topic').value
        self.pub = self.create_publisher(BatteryState, topic, 10)

        from_topic = self.get_parameter('from_topic').value
        if from_topic:
            self._setup_topic_source(from_topic)
        else:
            self._setup_serial_source()

        rate = float(self.get_parameter('rate').value)
        self.create_timer(1.0 / max(rate, 0.1), self.publish_state)
        self.get_logger().info(f'Publikuje {topic}, ogniw: {self.cells}')

    # ---------------- źródło: topic (gdy port trzyma sterownik) -------------

    def _setup_topic_source(self, topic):
        field = self.get_parameter('voltage_field').value
        self.get_logger().info(f'Napiecie z topicu {topic}, pole "{field}"')
        try:
            from std_msgs.msg import Float32
            self.create_subscription(Float32, topic,
                                     lambda m: self._set_voltage(m.data), 10)
        except Exception as e:
            self.get_logger().error(f'Nie moge zasubskrybowac {topic}: {e}')

    # ---------------- źródło: port szeregowy --------------------------------

    def _setup_serial_source(self):
        port = self.get_parameter('port').value
        baud = int(self.get_parameter('baud').value)
        try:
            import serial
        except ImportError:
            self.get_logger().error('Brak pyserial: pip3 install pyserial')
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
        except Exception as e:
            self.get_logger().error(
                f'Nie moge otworzyc {port}: {e}. '
                f'Jesli port trzyma sterownik UGV, uzyj parametru from_topic.')
            return
        self.get_logger().info(f'Czytam telemetrie z {port}')
        t = threading.Thread(target=self._serial_loop, daemon=True)
        t.start()

    def _serial_loop(self):
        """Płytka UGV02 sama nadaje telemetrię w formacie JSON."""
        while rclpy.ok():
            try:
                raw = self.ser.readline().decode('utf-8', 'ignore').strip()
            except Exception:
                continue
            if not raw or not raw.startswith('{'):
                continue
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            # nazwa pola bywa różna zależnie od wersji firmware
            for key in ('v', 'voltage', 'bat', 'battery'):
                if key in d:
                    try:
                        self._set_voltage(float(d[key]))
                    except (TypeError, ValueError):
                        pass
                    break
            for key in ('current', 'i', 'amp'):
                if key in d:
                    try:
                        with self._lock:
                            self.current = float(d[key])
                    except (TypeError, ValueError):
                        pass
                    break

    # ---------------- wspólne ----------------------------------------------

    def _set_voltage(self, v):
        """Wygładzanie — surowy odczyt skacze przy ruszaniu silników."""
        if not math.isfinite(v):
            return
        with self._lock:
            if math.isnan(self.voltage):
                self.voltage = v
            else:
                self.voltage = (1 - self.alpha) * self.voltage + self.alpha * v

    def publish_state(self):
        with self._lock:
            v = self.voltage
            i = self.current

        if math.isnan(v):
            return          # jeszcze nic nie przyszło — nie publikuj śmieci

        m = BatteryState()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = 'base_link'
        m.voltage = float(v)
        m.current = float(i) if math.isfinite(i) else float('nan')
        m.percentage = float(soc_from_voltage(v, self.cells))
        m.charge = float('nan')
        m.capacity = float('nan')
        m.design_capacity = float('nan')
        m.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
        m.present = True

        per_cell = v / self.cells if self.cells else 0.0
        if per_cell < 3.2:
            m.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_DEAD
        elif per_cell > 4.3:
            m.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_OVERVOLTAGE
        else:
            m.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD

        if math.isfinite(i) and i > 0.05:
            m.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        elif math.isfinite(i) and i < -0.05:
            m.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        else:
            m.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_UNKNOWN

        self.pub.publish(m)

        # ostrzeżenie w logu — widać w journalctl nawet bez panelu
        if per_cell < 3.4:
            self.get_logger().warn(
                f'Niskie napiecie: {v:.2f} V ({per_cell:.2f} V/ogniwo) — laduj!',
                throttle_duration_sec=60)


def main():
    rclpy.init()
    node = BatteryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()