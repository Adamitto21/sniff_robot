import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

latest_frame = None
frame_lock = threading.Lock()

class MjpegHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # wyłącz logi HTTP

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <html><body style="background:#000;margin:0">
            <img src="/stream" style="width:100%;height:100vh;object-fit:contain">
            </body></html>
            ''')
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    with frame_lock:
                        frame = latest_frame
                    if frame is not None:
                        _, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        self.wfile.write(b'--frame\r\n')
                        self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                        self.wfile.write(jpg.tobytes())
                        self.wfile.write(b'\r\n')
                    threading.Event().wait(0.033)  # ~30 Hz max
            except Exception:
                pass

class WebViewerNode(Node):
    def __init__(self):
        super().__init__('web_viewer')
        self.declare_parameter('port', 8080)
        port = self.get_parameter('port').value

        self.bridge = CvBridge()
        self.sub = self.create_subscription(
            Image,
            '/sniff/camera/image',
            self.image_callback,
            10
        )

        # Uruchom serwer HTTP w osobnym wątku
        server = HTTPServer(('0.0.0.0', port), MjpegHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        self.get_logger().info(f'Web viewer dostępny na http://0.0.0.0:{port}')
        self.get_logger().info(f'Otwórz w przeglądarce: http://JETSON_IP:{port}')

    def image_callback(self, msg):
        global latest_frame
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        with frame_lock:
            latest_frame = frame

def main(args=None):
    rclpy.init(args=args)
    node = WebViewerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
