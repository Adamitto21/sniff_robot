import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import depthai as dai
import numpy as np
import cv2
import os
from ament_index_python.packages import get_package_share_directory

LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush"
]

class OakDetectorNode(Node):
    def __init__(self):
        super().__init__('oak_detector')

        self.declare_parameter('blob_path', '')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('fps', 15)

        blob_path = self.get_parameter('blob_path').value
        if not blob_path:
            pkg_dir = get_package_share_directory('sniff_vision')
            blob_path = os.path.join(pkg_dir, 'models', 'yolov8n.blob')

        self.conf_thresh = self.get_parameter('confidence_threshold').value
        fps = self.get_parameter('fps').value

        self.get_logger().info(f'Ładowanie modelu: {blob_path}')

        self.pub_detections = self.create_publisher(Detection2DArray, '/detections', 10)
        self.pub_image = self.create_publisher(Image, '/sniff/camera/image', 10)
        self.bridge = CvBridge()

        self.device, self.q_rgb, self.q_nn = self._build_pipeline(blob_path, fps)
        self.get_logger().info('Kamera i model gotowe ✓')

        self.create_timer(1.0 / fps, self.process_frame)

    def _build_pipeline(self, blob_path, fps):
        # depthai 2.x API
        pipeline = dai.Pipeline()

        cam_rgb = pipeline.create(dai.node.ColorCamera)
        nn = pipeline.create(dai.node.NeuralNetwork)
        xout_rgb = pipeline.createXLinkOut()
        xout_nn = pipeline.createXLinkOut()

        xout_rgb.setStreamName("rgb")
        xout_nn.setStreamName("nn")

        cam_rgb.setPreviewSize(416, 416)
        cam_rgb.setInterleaved(False)
        cam_rgb.setFps(fps)

        nn.setBlobPath(blob_path)
        nn.input.setBlocking(False)
        nn.input.setQueueSize(1)

        cam_rgb.preview.link(nn.input)
        cam_rgb.preview.link(xout_rgb.input)
        nn.out.link(xout_nn.input)

        device = dai.Device(pipeline)

        q_rgb = device.getOutputQueue("rgb", maxSize=4, blocking=False)
        q_nn = device.getOutputQueue("nn", maxSize=4, blocking=False)

        return device, q_rgb, q_nn

    def process_frame(self):
        in_rgb = self.q_rgb.tryGet()
        in_nn = self.q_nn.tryGet()

        if in_rgb is None:
            return

        frame = in_rgb.getCvFrame()
        h, w = frame.shape[:2]

        det_array = Detection2DArray()
        det_array.header.stamp = self.get_clock().now().to_msg()
        det_array.header.frame_id = 'oak_camera'

        if in_nn is not None:
            output = np.array(in_nn.getFirstLayerFp16())
            output = output.reshape(84, -1).T  # (3549, 84)

            boxes = output[:, :4]
            scores = output[:, 4:]

            class_ids = np.argmax(scores, axis=1)
            confidences = scores[np.arange(len(scores)), class_ids]

            mask = confidences > self.conf_thresh
            boxes = boxes[mask]
            confidences = confidences[mask]
            class_ids = class_ids[mask]

            for box, conf, cls_id in zip(boxes, confidences, class_ids):
                cx, cy, bw, bh = box
                x1 = int((cx - bw / 2) * w)
                y1 = int((cy - bh / 2) * h)
                x2 = int((cx + bw / 2) * w)
                y2 = int((cy + bh / 2) * h)

                label = LABELS[cls_id] if cls_id < len(LABELS) else str(cls_id)

                det = Detection2D()
                det.header = det_array.header
                det.bbox.center.position.x = float(cx * w)
                det.bbox.center.position.y = float(cy * h)
                det.bbox.size_x = float(bw * w)
                det.bbox.size_y = float(bh * h)
                hyp = ObjectHypothesisWithPose()
                hyp.hypothesis.class_id = label
                hyp.hypothesis.score = float(conf)
                det.results.append(hyp)
                det_array.detections.append(det)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{label} {conf:.2f}',
                            (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 1)

        self.pub_detections.publish(det_array)
        img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        img_msg.header = det_array.header
        self.pub_image.publish(img_msg)


def main(args=None):
    rclpy.init(args=args)
    node = OakDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.device.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
