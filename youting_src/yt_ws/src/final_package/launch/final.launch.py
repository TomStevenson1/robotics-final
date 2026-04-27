from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    # Video Publisher Node
    # video_pub_node = Node(
    #     package='hw05_package',
    #     executable='video_publisher_node',
    #     name='video_publisher',
    #     parameters=[{
    #         'video_path': '/home/liu03745/hw05/trackvideo.mp4',
    #         'image_topic': '/camera/image_raw',
    #         'fps': 10.0,
    #         'loop': True
    #     }]
    # )
    
    move_control_node = Node(
        package='final_package',
        executable='move_control_node',
        name='move_control_node',
    )
    
    emergency_brake_node = Node(
        package='final_package',
        executable='emergency_brake_node',
        name='emergency_brake_node',
    )

    return LaunchDescription([
        # video_pub_node,
        move_control_node,
        emergency_brake_node
    ])