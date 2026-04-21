# esp32_camera_bridge

This ROS 2 Humble package connects to the ESP32 camera's MJPEG stream and
republishes each decoded frame as a `sensor_msgs/msg/Image` message.

## ESP32 stream

The Arduino code exposes the stream at:

`http://<esp32-ip>/stream`

## Build

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Run

```bash
ros2 run esp32_camera_bridge mjpeg_image_publisher --ros-args -p stream_url:=http://192.168.1.50/stream
```

Or use the launch file:

```bash
ros2 launch esp32_camera_bridge esp32_camera_bridge.launch.py stream_url:=http://192.168.1.50/stream
```

The default topic is `/esp32/camera/image_raw`.
