from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'stream_url',
            default_value='http://192.168.1.100/stream',
            description='ESP32 MJPEG stream URL.',
        ),
        DeclareLaunchArgument(
            'topic',
            default_value='/esp32/camera/image_raw',
            description='ROS 2 image topic to publish.',
        ),
        DeclareLaunchArgument(
            'frame_id',
            default_value='esp32_camera',
            description='Frame id written into the image header.',
        ),
        Node(
            package='esp32_camera_bridge',
            executable='mjpeg_image_publisher',
            name='esp32_mjpeg_image_publisher',
            output='screen',
            parameters=[{
                'stream_url': LaunchConfiguration('stream_url'),
                'topic': LaunchConfiguration('topic'),
                'frame_id': LaunchConfiguration('frame_id'),
            }],
        ),
    ])