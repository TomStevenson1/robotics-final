import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import TwistStamped

class ControlNode(Node):
    def __init__(self):
        super().__init__('robot_control_node')
        
        # Subscribe to the emergency stop signal
        self.emergency_sub = self.create_subscription(
            Bool, '/emergency_stop_signal', self.emergency_callback, 10)
        
        # Publisher for velocity commands
        self.cmd_vel_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        
        self.is_emergency = False
        
        # Timer to control the robot at a fixed rate
        self.timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info("Move control node initialized...")

    def emergency_callback(self, msg):
        self.is_emergency = msg.data

    def control_loop(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        if self.is_emergency:
            msg.twist.linear.x = 0.0
            self.get_logger().warn("Obstacle detected! Stopping...", once=False)
        else:
            msg.twist.linear.x = 0.15
            # self.get_logger().info("Safe ahead, moving forward...")

        self.cmd_vel_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # For safety, send the last stop command before shutting down
        stop_msg = TwistStamped()
        stop_msg.header.stamp = node.get_clock().now().to_msg()
        node.cmd_vel_pub.publish(stop_msg)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()