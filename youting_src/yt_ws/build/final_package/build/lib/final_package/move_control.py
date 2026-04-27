import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import TwistStamped

class ControlNode(Node):
    def __init__(self):
        super().__init__('robot_control_node')
        
        # 訂閱緊急訊號
        self.emergency_sub = self.create_subscription(
            Bool, '/emergency_stop_signal', self.emergency_callback, 10)
        
        # 最終的速度發佈者 (Gazebo Sim 需要 TwistStamped)
        self.cmd_vel_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        
        self.is_emergency = False
        
        # 建立定時器，每 0.1 秒執行一次控制迴圈 (10Hz)
        self.timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info("控制節點已啟動：準備接收訊號控制輪子...")

    def emergency_callback(self, msg):
        # 更新當前是否有障礙物的狀態
        self.is_emergency = msg.data

    def control_loop(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        if self.is_emergency:
            # 發現障礙物，強制停下
            msg.twist.linear.x = 0.0
            self.get_logger().warn("🚨 偵測到危險！停止中...", once=False)
        else:
            # 安全狀態，穩定前進
            msg.twist.linear.x = 0.15
            # self.get_logger().info("🟢 前方安全，穩定前進中...")

        self.cmd_vel_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 安全起見，結束前發送最後一個停止指令
        stop_msg = TwistStamped()
        stop_msg.header.stamp = node.get_clock().now().to_msg()
        node.cmd_vel_pub.publish(stop_msg)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()