import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from geometry_msgs.msg import TwistStamped


class ControlNode(Node):
    def __init__(self):
        super().__init__('move_control_node')

        self.declare_parameter('speeds.forward', 0.15)
        self.declare_parameter('speeds.reverse', -0.10)
        self.declare_parameter('speeds.turn', 0.5)
        self.declare_parameter('watchdog_timeout', 3.0)

        gesture_defaults = {
            'gestures.Pointing_Up': 'forward',
            'gestures.Victory': 'reverse',
            'gestures.Open_Palm': 'stop',
            'gestures.Closed_Fist': 'stop',
            'gestures.Thumb_Up_Left': 'turn_left',
            'gestures.Thumb_Up_Right': 'turn_right',
            'gestures.Thumb_Down': '',
            'gestures.ILoveYou': '',
            'gestures.None': 'stop',
        }
        for key, default in gesture_defaults.items():
            self.declare_parameter(key, default)

        self.speed_forward = self.get_parameter('speeds.forward').value
        self.speed_reverse = self.get_parameter('speeds.reverse').value
        self.speed_turn = self.get_parameter('speeds.turn').value
        self.watchdog_timeout = self.get_parameter('watchdog_timeout').value

        self.gesture_map = {}
        for key in gesture_defaults:
            gesture_name = key.split('.', 1)[1]
            self.gesture_map[gesture_name] = self.get_parameter(key).value

        self.emergency_sub = self.create_subscription(
            Bool, '/emergency_stop_signal', self.emergency_callback, 10)
        self.gesture_sub = self.create_subscription(
            String, '/gesture_signal', self.gesture_callback, 10)

        self.cmd_vel_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)

        self.is_emergency = False
        self.last_gesture_time = None
        self.current_gesture_msg = 'Left:None|Right:None'

        self.timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('Move control node initialized...')

    def emergency_callback(self, msg):
        self.is_emergency = msg.data

    def gesture_callback(self, msg):
        self.current_gesture_msg = msg.data
        self.last_gesture_time = self.get_clock().now()

    def resolve_action(self, hand, gesture):
        compound_key = f'{gesture}_{hand}'
        if compound_key in self.gesture_map:
            return self.gesture_map[compound_key] or None
        action = self.gesture_map.get(gesture)
        return action or None

    def compute_twist(self, gesture_msg):
        parts = gesture_msg.split('|')
        if len(parts) != 2:
            return (0.0, 0.0)

        actions = set()
        for part in parts:
            tokens = part.split(':', 1)
            if len(tokens) != 2:
                continue
            hand, gesture = tokens[0], tokens[1]
            action = self.resolve_action(hand, gesture)
            if action:
                actions.add(action)

        if not actions or 'stop' in actions:
            return (0.0, 0.0)

        has_forward = 'forward' in actions
        has_reverse = 'reverse' in actions
        has_turn_left = 'turn_left' in actions
        has_turn_right = 'turn_right' in actions

        if (has_forward and has_reverse) or (has_turn_left and has_turn_right):
            return (0.0, 0.0)

        linear_x = 0.0
        angular_z = 0.0

        if has_forward:
            linear_x = self.speed_forward
        elif has_reverse:
            linear_x = self.speed_reverse

        if has_turn_left:
            angular_z = self.speed_turn
        elif has_turn_right:
            angular_z = -self.speed_turn

        return (linear_x, angular_z)

    def control_loop(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        if self.is_emergency:
            self.get_logger().warn('Obstacle detected! Stopping...')
            self.cmd_vel_pub.publish(msg)
            return

        if self.last_gesture_time is None:
            self.cmd_vel_pub.publish(msg)
            return

        elapsed = (self.get_clock().now() - self.last_gesture_time).nanoseconds / 1e9
        if elapsed > self.watchdog_timeout:
            self.get_logger().warn('Gesture signal lost, stopping...')
            self.cmd_vel_pub.publish(msg)
            return

        linear_x, angular_z = self.compute_twist(self.current_gesture_msg)
        msg.twist.linear.x = linear_x
        msg.twist.angular.z = angular_z
        self.cmd_vel_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            stop_msg = TwistStamped()
            stop_msg.header.stamp = node.get_clock().now().to_msg()
            node.cmd_vel_pub.publish(stop_msg)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
