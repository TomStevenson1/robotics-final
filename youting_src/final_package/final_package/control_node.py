import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, Twist

class ControlNode(Node):
    def __init__(self):
        super().__init__('control_node')
        # subscription
        self.sub = self.create_subscription(Point, '/target/center', self.control_callback, 10)
        # publisher
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

    def control_callback(self, msg):
        twist = Twist()
        
        # If no target detected, msg.z will be negative frame width.
        # Otherwise, msg.z is the frame width.
        
        if msg.z <= 0:
            # searching behavior: rotate in place
            twist.angular.z = 0.5
            twist.linear.x = 0.0
        else:
            # tracking behavior: proportional control to center the target
            error_x = msg.x - (msg.z / 2)
            twist.angular.z = -error_x * 0.005
            twist.linear.x = 1.0
            
        self.cmd_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(ControlNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()