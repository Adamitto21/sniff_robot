import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


latest_frame = None
latest_depth_frame = None  # NOWEThreadingHTTPServer
frame_lock = threading.Lock()
depth_lock = threading.Lock()  # NOWE

class MjpegHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <html><body style="background:#000;margin:0">
            <div style="display:flex;height:100vh">
                <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center">
                    <p style="color:#fff;font-family:sans-serif">Kolor + detekcje</p>
                    <img src="/stream" style="max-width:100%;max-height:90vh;object-fit:contain">
                </div>
                <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center">
                    <p style="color:#fff;font-family:sans-serif">Glebia</p>
                    <img src="/depth_stream" style="max-width:100%;max-height:90vh;object-fit:contain">
                </div>
            </div>
            </body></html>
            ''')
        elif self.path == '/stream':
            self._stream(frame_lock, lambda: latest_frame)
        elif self.path == '/depth_stream':  # NOWE
            self._stream(depth_lock, lambda: latest_depth_frame)

    def _stream(self, lock, get_frame):
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        try:
            while True:
                with lock:
                    frame = get_frame()
                if frame is not None:
                    _, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(jpg.tobytes())
                    self.wfile.write(b'\r\n')
                threading.Event().wait(0.033)
        except Exception:
            pass

class WebViewerNode(Node):
    def __init__(self):
        super().__init__('web_viewer')
        self.declare_parameter('port', 8080)
        port = self.get_parameter('port').value

        self.bridge = CvBridge()
        self.sub = self.create_subscription(
            Image, '/sniff/camera/image', self.image_callback, 10
        )
        self.sub_depth = self.create_subscription(  # NOWE
            Image, '/sniff/camera/depth/preview', self.depth_callback, 10
        )

        server = ThreadingHTTPServer(('0.0.0.0', port), MjpegHandler)  # zmiana z HTTPServer
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        self.get_logger().info(f'Web viewer dostepny na http://0.0.0.0:{port}')
        self.get_logger().info(f'Otworz w przegladarce: http://JETSON_IP:{port}')

    def image_callback(self, msg):
        global latest_frame
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        with frame_lock:
            latest_frame = frame

    def depth_callback(self, msg):  # NOWE
        global latest_depth_frame
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        with depth_lock:
            latest_depth_frame = frame

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