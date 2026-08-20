import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField
from std_msgs.msg import Header
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import depthai as dai
import numpy as np
import cv2
import os
import time
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
        self.declare_parameter('fps', 10)
        self.declare_parameter('depth_point_step', 8)

        blob_path = self.get_parameter('blob_path').value
        if not blob_path:
            pkg_dir = get_package_share_directory('sniff_vision')
            blob_path = os.path.join(pkg_dir, 'models', 'yolov5n.blob')

        self.conf_thresh = self.get_parameter('confidence_threshold').value
        self.fps = self.get_parameter('fps').value
        self.point_step_px = self.get_parameter('depth_point_step').value

        self.get_logger().info(
            f'Ladowanie modelu: {blob_path}, fps={self.fps}')

        self.pub_detections = self.create_publisher(
            Detection2DArray, '/detections', 10)
        self.pub_image = self.create_publisher(
            Image, '/sniff/camera/image', 10)
        self.pub_points = self.create_publisher(
            PointCloud2, '/sniff/oak_d_lite_depth/points', 5)
        self.bridge = CvBridge()

        (self.device, self.q_rgb, self.q_nn, self.q_depth,
         self.intrinsics) = self._build_pipeline(blob_path)

        self.get_logger().info('Kamera, YOLO i stereo depth gotowe')
        self.create_timer(1.0 / self.fps, self.process_frame)

    def _build_pipeline(self, blob_path):
        pipeline = dai.Pipeline()

        # ---------- RGB + YOLO ----------
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        nn = pipeline.create(dai.node.YoloDetectionNetwork)
        xout_rgb = pipeline.createXLinkOut()
        xout_nn = pipeline.createXLinkOut()
        xout_rgb.setStreamName("rgb")
        xout_nn.setStreamName("nn")

        cam_rgb.setPreviewSize(416, 416)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        cam_rgb.setFps(self.fps)

        nn.setBlobPath(blob_path)
        nn.setConfidenceThreshold(self.conf_thresh)
        nn.setNumClasses(80)
        nn.setCoordinateSize(4)
        nn.setIouThreshold(0.5)
        nn.setAnchors([
            10, 13, 16, 30, 33, 23,
            30, 61, 62, 45, 59, 119,
            116, 90, 156, 198, 373, 326
        ])
        nn.setAnchorMasks({
            "side52": [0, 1, 2],
            "side26": [3, 4, 5],
            "side13": [6, 7, 8]
        })
        nn.input.setBlocking(False)
        nn.input.setQueueSize(1)

        cam_rgb.preview.link(nn.input)
        cam_rgb.preview.link(xout_rgb.input)
        nn.out.link(xout_nn.input)

        # ---------- Stereo depth ----------
        mono_left = pipeline.create(dai.node.MonoCamera)
        mono_right = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)
        xout_depth = pipeline.createXLinkOut()
        xout_depth.setStreamName("depth")

        mono_left.setResolution(
            dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
        mono_left.setFps(self.fps)

        mono_right.setResolution(
            dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
        mono_right.setFps(self.fps)

        stereo.initialConfig.setConfidenceThreshold(200)
        stereo.setLeftRightCheck(True)
        stereo.setSubpixel(False)
        stereo.setExtendedDisparity(False)
        stereo.setDepthAlign(dai.CameraBoardSocket.RIGHT)

        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)
        stereo.depth.link(xout_depth.input)

        device = dai.Device(pipeline)

        q_rgb = device.getOutputQueue("rgb", maxSize=4, blocking=False)
        q_nn = device.getOutputQueue("nn", maxSize=4, blocking=False)
        q_depth = device.getOutputQueue("depth", maxSize=4, blocking=False)

        calib = device.readCalibration()
        intr = calib.getCameraIntrinsics(dai.CameraBoardSocket.RIGHT, 640, 400)
        intrinsics = {
            'fx': intr[0][0], 'fy': intr[1][1],
            'cx': intr[0][2], 'cy': intr[1][2],
        }

        return device, q_rgb, q_nn, q_depth, intrinsics

    def process_frame(self):
        in_rgb = self.q_rgb.tryGet()
        in_nn = self.q_nn.tryGet()
        in_depth = self.q_depth.tryGet()

        if in_rgb is not None:
            self._publish_detections(in_rgb, in_nn)

        if in_depth is not None:
            self._publish_pointcloud(in_depth)

    def _publish_detections(self, in_rgb, in_nn):
        frame = in_rgb.getCvFrame()
        h, w = frame.shape[:2]

        det_array = Detection2DArray()
        det_array.header.stamp = self.get_clock().now().to_msg()
        det_array.header.frame_id = 'oak_camera'

        if in_nn is not None:
            for det in in_nn.detections:
                label = LABELS[det.label] if det.label < len(LABELS) else str(det.label)
                x1 = int(det.xmin * w)
                y1 = int(det.ymin * h)
                x2 = int(det.xmax * w)
                y2 = int(det.ymax * h)

                ros_det = Detection2D()
                ros_det.header = det_array.header
                ros_det.bbox.center.position.x = float((x1 + x2) / 2)
                ros_det.bbox.center.position.y = float((y1 + y2) / 2)
                ros_det.bbox.size_x = float(x2 - x1)
                ros_det.bbox.size_y = float(y2 - y1)
                hyp = ObjectHypothesisWithPose()
                hyp.hypothesis.class_id = label
                hyp.hypothesis.score = float(det.confidence)
                ros_det.results.append(hyp)
                det_array.detections.append(ros_det)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{label} {det.confidence:.2f}',
                            (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        self.pub_detections.publish(det_array)
        img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        img_msg.header = det_array.header
        self.pub_image.publish(img_msg)

    def _publish_pointcloud(self, in_depth):
        t_start = time.perf_counter()    
        depth_frame = in_depth.getFrame()  # uint16, milimetry
        step = self.point_step_px

        v_idx, u_idx = np.mgrid[0:depth_frame.shape[0]:step,
                                 0:depth_frame.shape[1]:step]
        z = depth_frame[v_idx, u_idx].astype(np.float32) / 1000.0  # mm -> m

        valid = z > 0.1
        z = z[valid]
        u = u_idx[valid].astype(np.float32)
        v = v_idx[valid].astype(np.float32)

        fx, fy = self.intrinsics['fx'], self.intrinsics['fy']
        cx, cy = self.intrinsics['cx'], self.intrinsics['cy']

        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        points = np.stack([x, y, z], axis=-1).astype(np.float32)

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera_link_optical'

        msg = PointCloud2()
        msg.header = header
        msg.height = 1
        msg.width = points.shape[0]
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = 12 * points.shape[0]
        msg.is_dense = True
        msg.data = points.tobytes()

        self.pub_points.publish(msg)
        t_elapsed = (time.perf_counter() - t_start) * 1000

        now = time.time()
        last_log = getattr(self, '_last_telemetry_log', 0.0)
        if now - last_log >= 60.0:
            self._last_telemetry_log = now
            css = self.device.getChipTemperature()
            self.get_logger().info(
                f'Reprojekcja point cloud: {t_elapsed:.2f} ms, '
                f'{points.shape[0]} punktow, '
                f'temp VPU avg: {css.average:.1f}C')

            if css.average > 70.0:
                self.get_logger().warn(
                    f'VPU temperatura wysoka: {css.average:.1f}C (prog: 70.0C)')

        if t_elapsed > 20.0:
            self.get_logger().warn(
                f'Reprojekcja point cloud wolna: {t_elapsed:.2f} ms (prog: 20.0 ms)')

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
