import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory('final_package'),
        'config', 'params.yaml'
    )

    move_control_node = Node(
        package='final_package',
        executable='move_control_node',
        name='move_control_node',
        parameters=[params_file],
    )

    emergency_brake_node = Node(
        package='final_package',
        executable='emergency_brake_node',
        name='emergency_brake_node',
        parameters=[params_file],
    )

    return LaunchDescription([
        move_control_node,
        emergency_brake_node,
    ])
