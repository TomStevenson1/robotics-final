import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
import cv2
import numpy as np

class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')
        
        # HSV color range parameters (Initial values for green color)
        self.declare_parameter('low_h', 40)
        self.declare_parameter('low_s', 40)
        self.declare_parameter('low_v', 40)
        self.declare_parameter('high_h', 80)
        self.declare_parameter('high_s', 255)
        self.declare_parameter('high_v', 255)

        # subscription
        self.sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        # publisher
        self.pos_pub = self.create_publisher(Point, '/target/center', 10)
        self.bridge = CvBridge()

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # retrieve HSV parameters
        low_h = self.get_parameter('low_h').value
        low_s = self.get_parameter('low_s').value
        low_v = self.get_parameter('low_v').value
        high_h = self.get_parameter('high_h').value
        high_s = self.get_parameter('high_s').value
        high_v = self.get_parameter('high_v').value

        lower_color = np.array([low_h, low_s, low_v]) 
        upper_color = np.array([high_h, high_s, high_v])
        
        mask = cv2.inRange(hsv, lower_color, upper_color)
        
        ys, xs = np.where(mask == 255)
        
        msg_point = Point()
        if len(xs) > 0:
            msg_point.x = float(np.mean(xs)) # center x
            msg_point.y = float(np.mean(ys)) # center y
            msg_point.z = float(frame.shape[1]) # frame width
        else:
            msg_point.x = 0.0
            msg_point.y = 0.0
            msg_point.z = -float(frame.shape[1]) # negative frame width to indicate no target
            
        self.pos_pub.publish(msg_point)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(PerceptionNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()