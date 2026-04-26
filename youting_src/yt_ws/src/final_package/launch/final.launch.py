from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    # Video Publisher Node
    video_pub_node = Node(
        package='hw05_package',
        executable='video_publisher_node',
        name='video_publisher',
        parameters=[{
            'video_path': '/home/liu03745/hw05/trackvideo.mp4',
            'image_topic': '/camera/image_raw',
            'fps': 10.0,
            'loop': True
        }]
    )

    return LaunchDescription([
        video_pub_node,
    ])