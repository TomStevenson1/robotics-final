import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class EmergencyBrakeNode(Node):
    def __init__(self):
        super().__init__('emergency_brake_node')
        
        # 建立訂閱者，監聽光達數據
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10)
        
        # 建立發佈者，控制機器人速度
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 設定安全距離（公尺）
        self.safe_distance = 0.5 
        self.is_obstacle_ahead = False

    def scan_callback(self, msg):
        # 獲取正前方（0度附近）的掃描距離
        # LaserScan 的 ranges 陣列通常 0 度是在正前方
        # 我們取前方一小個扇形區域以增加穩定性
        front_ranges = msg.ranges[0:15] + msg.ranges[345:359]
        
        # 過濾掉 0 (無效數據)，並找到最小距離
        valid_ranges = [r for r in front_ranges if r > msg.range_min]
        min_distance = min(valid_ranges) if valid_ranges else float('inf')

        if min_distance < self.safe_distance:
            if not self.is_obstacle_ahead:
                self.get_logger().warn(f"偵測到障礙物！距離: {min_distance:.2f}m，停止移動。")
                self.is_obstacle_ahead = True
                self.stop_robot()
        else:
            self.is_obstacle_ahead = False
            self.move_forward()

    def move_forward(self):
        msg = Twist()
        msg.linear.x = 0.15  # 向前移動速度
        self.cmd_vel_pub.publish(msg)

    def stop_robot(self):
        msg = Twist()
        msg.linear.x = 0.0   # 停止
        self.cmd_vel_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = EmergencyBrakeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()