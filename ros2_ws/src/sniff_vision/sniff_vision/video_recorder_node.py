import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import time
import glob


class VideoRecorderNode(Node):
    def __init__(self):
        super().__init__('video_recorder')

        self.declare_parameter('output_dir', '/ros2_ws/recordings')
        self.declare_parameter('clip_duration_sec', 120)
        self.declare_parameter('max_clips', 8)
        self.declare_parameter('fps', 5)
        self.declare_parameter('image_topic', '/sniff/camera/image')

        self.output_dir = self.get_parameter('output_dir').value
        self.clip_duration = self.get_parameter('clip_duration_sec').value
        self.max_clips = self.get_parameter('max_clips').value
        self.fps = self.get_parameter('fps').value

        os.makedirs(self.output_dir, exist_ok=True)

        self.bridge = CvBridge()
        self.writer = None
        self.clip_start_time = None
        self.frame_size = None

        image_topic = self.get_parameter('image_topic').value
        self.sub = self.create_subscription(
            Image, image_topic, self.image_callback, 10)

        self.get_logger().info(
            f'Nagrywanie z {image_topic} do {self.output_dir}, '
            f'klipy po {self.clip_duration}s, max {self.max_clips} plikow')

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        h, w = frame.shape[:2]

        now = time.time()

        # Nowy klip: brak writera lub minal czas
        if self.writer is None or (now - self.clip_start_time) >= self.clip_duration:
            self._start_new_clip(w, h)

        self.writer.write(frame)

    def _start_new_clip(self, w, h):
        if self.writer is not None:
            self.writer.release()
            self._cleanup_old_clips()

        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.output_dir, f'sniff_{timestamp}.mp4')

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(filepath, fourcc, self.fps, (w, h))
        self.clip_start_time = time.time()
        self.frame_size = (w, h)

        self.get_logger().info(f'Nowy klip: {filepath}')

    def _cleanup_old_clips(self):
        clips = sorted(
            glob.glob(os.path.join(self.output_dir, 'sniff_*.mp4')),
            key=os.path.getmtime
        )
        while len(clips) > self.max_clips:
            oldest = clips.pop(0)
            os.remove(oldest)
            self.get_logger().info(f'Usunieto stary klip: {oldest}')

    def destroy_node(self):
        if self.writer is not None:
            self.writer.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VideoRecorderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

