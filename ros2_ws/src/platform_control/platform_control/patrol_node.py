#!/usr/bin/env python3
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.time import Time as RclTime

from nav2_msgs.action import NavigateToPose
from visualization_msgs.msg import MarkerArray
from action_msgs.msg import GoalStatus

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener


class PatrolNode(Node):
    def __init__(self):
        super().__init__('patrol_node')

        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('frontiers_topic', '/explore/frontiers')
        self.declare_parameter('waypoint_distance_m', 2.0)
        self.declare_parameter('waypoint_time_sec', 60.0)
        self.declare_parameter('waypoint_merge_radius_m', 1.0)
        self.declare_parameter('frontier_empty_threshold_sec', 15.0)
        self.declare_parameter('patrol_goal_timeout_sec', 180.0)

        self.map_frame = self.get_parameter('map_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.waypoint_distance = self.get_parameter('waypoint_distance_m').value
        self.waypoint_time = self.get_parameter('waypoint_time_sec').value
        self.merge_radius = self.get_parameter('waypoint_merge_radius_m').value
        self.frontier_empty_threshold = self.get_parameter(
            'frontier_empty_threshold_sec').value
        self.patrol_timeout = self.get_parameter('patrol_goal_timeout_sec').value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.waypoints = []  # [{'x':, 'y':, 'last_visited':}, ...]
        self.last_waypoint_pos = None
        self.last_waypoint_time = time.time()

        self.state = 'EXPLORING'  # albo 'PATROLLING'
        self.frontiers_empty_since = None

        self.current_goal_handle = None
        self.current_patrol_target = None
        self.goal_start_time = None

        frontiers_topic = self.get_parameter('frontiers_topic').value
        self.sub_frontiers = self.create_subscription(
            MarkerArray, frontiers_topic, self.frontiers_callback, 10)

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.create_timer(0.5, self.position_timer_callback)
        self.create_timer(2.0, self.state_check_callback)
        self.create_timer(2.0, self.patrol_timer_callback)
        self.create_timer(60.0, self.telemetry_callback)

        self.get_logger().info(
            f'Patrol node gotowy. Prog pustych granic: {self.frontier_empty_threshold}s, '
            f'timeout celu patrolu: {self.patrol_timeout}s')

    # ---------- Sledzenie pozycji i zapis waypointow ----------

    def position_timer_callback(self):
        try:
            t = self.tf_buffer.lookup_transform(
                self.map_frame, self.base_frame, RclTime())
        except TransformException:
            return

        x = t.transform.translation.x
        y = t.transform.translation.y
        now = time.time()

        if self.last_waypoint_pos is None:
            self._record_or_refresh_waypoint(x, y, now)
            return

        dist = math.hypot(x - self.last_waypoint_pos[0], y - self.last_waypoint_pos[1])
        elapsed = now - self.last_waypoint_time
        if dist >= self.waypoint_distance or elapsed >= self.waypoint_time:
            self._record_or_refresh_waypoint(x, y, now)

    def _record_or_refresh_waypoint(self, x, y, now):
        # Jesli jestesmy blisko istniejacego punktu, tylko odswiez jego timestamp
        # zamiast tworzyc duplikat obok.
        for wp in self.waypoints:
            if math.hypot(x - wp['x'], y - wp['y']) < self.merge_radius:
                wp['last_visited'] = now
                self.last_waypoint_pos = (x, y)
                self.last_waypoint_time = now
                return

        self.waypoints.append({'x': x, 'y': y, 'last_visited': now})
        self.last_waypoint_pos = (x, y)
        self.last_waypoint_time = now

    # ---------- Monitorowanie granic (frontiers) ----------

    def frontiers_callback(self, msg):
        now = time.time()
        if len(msg.markers) == 0:
            if self.frontiers_empty_since is None:
                self.frontiers_empty_since = now
        else:
            self.frontiers_empty_since = None
            if self.state == 'PATROLLING':
                self.get_logger().info(
                    'Wykryto nowa granice - wracam do trybu eksploracji, '
                    'explore_lite przejmie nawigacje')
                self.state = 'EXPLORING'
                self._cancel_current_goal()

    def state_check_callback(self):
        if self.state == 'EXPLORING' and self.frontiers_empty_since is not None:
            elapsed = time.time() - self.frontiers_empty_since
            if elapsed >= self.frontier_empty_threshold:
                self.get_logger().info(
                    f'Brak granic przez {elapsed:.0f}s - przechodze w tryb patrolu '
                    f'({len(self.waypoints)} zapisanych punktow)')
                self.state = 'PATROLLING'

    # ---------- Wysylanie celow patrolu ----------

    def patrol_timer_callback(self):
        if self.state != 'PATROLLING':
            return

        if self.current_goal_handle is not None:
            if self.goal_start_time and \
                    (time.time() - self.goal_start_time) > self.patrol_timeout:
                self.get_logger().warn(
                    'Patrol: przekroczono timeout celu, anuluje i wybieram kolejny')
                self._cancel_current_goal()
            return  # cel juz w drodze

        self._send_next_patrol_goal()

    def _send_next_patrol_goal(self):
        if not self.waypoints:
            return

        target = min(self.waypoints, key=lambda w: w['last_visited'])
        self.current_patrol_target = target

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = self.map_frame
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = target['x']
        goal_msg.pose.pose.position.y = target['y']
        goal_msg.pose.pose.orientation.w = 1.0

        self.goal_start_time = time.time()

        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().warn('Patrol: serwer navigate_to_pose niedostepny')
            self.current_goal_handle = None
            return

        self.get_logger().info(
            f"Patrol: wysylam cel do ({target['x']:.2f}, {target['y']:.2f})")
        send_future = self._action_client.send_goal_async(goal_msg)
        send_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Patrol: cel odrzucony przez Nav2')
            self.current_goal_handle = None
            self.current_patrol_target = None
            return

        self.current_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._goal_result_callback)

    def _goal_result_callback(self, future):
        result = future.result()
        status = result.status

        if status == GoalStatus.STATUS_SUCCEEDED and self.current_patrol_target is not None:
            self.current_patrol_target['last_visited'] = time.time()
            self.get_logger().info('Patrol: cel osiagniety, odswiezono timestamp punktu')
        else:
            self.get_logger().info(
                f'Patrol: cel zakonczony ze statusem {status} '
                f'(wyparty przez explore_lite, timeout lub blad Nav2)')

        self.current_goal_handle = None
        self.current_patrol_target = None

    def _cancel_current_goal(self):
        if self.current_goal_handle is not None:
            self.current_goal_handle.cancel_goal_async()
            self.current_goal_handle = None
            self.current_patrol_target = None

    def telemetry_callback(self):
        self.get_logger().info(
            f'Patrol status: stan={self.state}, punkty={len(self.waypoints)}, '
            f'aktywny cel={"tak" if self.current_goal_handle else "nie"}')


def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
