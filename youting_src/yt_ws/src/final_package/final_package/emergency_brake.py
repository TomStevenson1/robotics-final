import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped  # 修改這裡：使用 TwistStamped
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import math

class EmergencyBrakeNode(Node):
    def __init__(self):
        super().__init__('emergency_brake_node')
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile)
        
        # 修改這裡：發佈類型改為 TwistStamped
        self.cmd_vel_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        
        self.safe_distance = 0.6 # 稍微調大一點點比較保險
        self.is_obstacle_ahead = False
        self.get_logger().info("緊急煞車節點已啟動 (Gazebo Sim 版本)")

    def scan_callback(self, msg):
        # 取得前方數據
        front_ranges = msg.ranges[0:20] + msg.ranges[340:359]
        valid_ranges = [r for r in front_ranges if math.isfinite(r) and r > msg.range_min]
        min_distance = min(valid_ranges) if valid_ranges else float('inf')

        if min_distance < self.safe_distance:
            self.stop_robot()
            if not self.is_obstacle_ahead:
                self.get_logger().warn(f"⚠️ 偵測到障礙物！距離: {min_distance:.2f}m")
                self.is_obstacle_ahead = True
        else:
            self.move_forward()
            self.is_obstacle_ahead = False

    def move_forward(self):
        msg = TwistStamped() # 修改這裡
        msg.header.stamp = self.get_clock().now().to_msg() # 填寫時間戳記
        msg.twist.linear.x = 0.15 
        self.cmd_vel_pub.publish(msg)

    def stop_robot(self):
        msg = TwistStamped() # 修改這裡
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = 0.0
        self.cmd_vel_pub.publish(msg)

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