import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import math

class EmergencyBrakeNode(Node):
    def __init__(self):
        super().__init__('emergency_detector')
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, qos_profile)
        
        # publisher for emergency stop signal
        self.emergency_pub = self.create_publisher(Bool, '/emergency_stop_signal', 10)
        
        self.safe_distance = 0.6
        self.get_logger().info("emergency brake node initialized...")

    def scan_callback(self, msg):
        # get the front 40 degrees (20 on each side)
        front_ranges = msg.ranges[0:20] + msg.ranges[340:359]
        valid_ranges = [r for r in front_ranges if math.isfinite(r) and r > msg.range_min]
        min_dist = min(valid_ranges) if valid_ranges else float('inf')

        emergency_msg = Bool()
        emergency_msg.data = min_dist < self.safe_distance
        self.emergency_pub.publish(emergency_msg)

def main(args=None):
    rclpy.init(args=args)
    node = EmergencyBrakeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()