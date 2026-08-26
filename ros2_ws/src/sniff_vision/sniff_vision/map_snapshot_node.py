import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
import numpy as np
import cv2
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

MAP_PATH = '/ros2_ws/map_snapshots/latest_map.png'


class MapHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''<html><body style="background:#222;margin:0">
            <img src="/map.png" style="width:100%;height:100vh;object-fit:contain">
            <p style="color:#aaa;font-family:monospace;position:fixed;top:0;left:0;padding:8px">
            Odswiez strone, zeby zobaczyc najnowsza zapisana mape.
            </p>
            </body></html>''')
        elif self.path == '/map.png':
            if os.path.exists(MAP_PATH):
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                with open(MAP_PATH, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()


class MapSnapshotNode(Node):
    def __init__(self):
        super().__init__('map_snapshot')
        self.declare_parameter('port', 8081)
        self.declare_parameter('save_interval_sec', 15.0)

        port = self.get_parameter('port').value
        self.save_interval = self.get_parameter('save_interval_sec').value

        os.makedirs(os.path.dirname(MAP_PATH), exist_ok=True)

        self.latest_grid = None

        qos = QoSProfile(
            depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )
        self.sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, qos)

        server = HTTPServer(('0.0.0.0', port), MapHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        self.create_timer(self.save_interval, self.save_snapshot)
        self.get_logger().info(
            f'Map snapshot viewer: http://0.0.0.0:{port}, '
            f'zapis co {self.save_interval}s do {MAP_PATH}')

    def map_callback(self, msg):
        self.latest_grid = msg

    def save_snapshot(self):
        if self.latest_grid is None:
            return

        msg = self.latest_grid
        w, h = msg.info.width, msg.info.height
        if w == 0 or h == 0:
            return

        data = np.array(msg.data, dtype=np.int16).reshape((h, w))

        img = np.full((h, w), 205, dtype=np.uint8)  # nieznane -> szare
        img[data == 0] = 254                         # wolne -> biale
        img[data == 100] = 0                          # zajete -> czarne
        mid = (data > 0) & (data < 100)
        img[mid] = (254 - (data[mid].astype(np.float32) / 100.0 * 254)).astype(np.uint8)

        img = np.flipud(img)  # konwencja ROS: wiersz 0 na dole

        tmp_path = MAP_PATH + '.tmp'
        cv2.imwrite(tmp_path, img)
        os.replace(tmp_path, MAP_PATH)  # atomowa podmiana pliku


def main(args=None):
    rclpy.init(args=args)
    node = MapSnapshotNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
