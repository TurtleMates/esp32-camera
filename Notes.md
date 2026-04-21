# Camera stream resolution

change in the CameraServerArduinoIDE.ino file the
set_framesize(s,FRAMESIZE_QVGA). here are the fields availble:

- FRAMESIZE_96X96
- FRAMESIZE_QQVGA (160x120)
- FRAMESIZE_QCIF (176x144)
- FRAMESIZE_HQVGA (240x176)
- FRAMESIZE_240X240
- FRAMESIZE_QVGA (320x240)
- FRAMESIZE_CIF (400x296)
- FRAMESIZE_HVGA (480x320)
- FRAMESIZE_VGA (640x480)
- FRAMESIZE_SVGA (800x600)
- FRAMESIZE_XGA (1024x768)
- FRAMESIZE_HD (1280x720)
- FRAMESIZE_SXGA (1280x1024)
- FRAMESIZE_UXGA (1600x1200)

# ROS 2 bridge for ESP32 stream (general guide)

This repository contains a ROS 2 package at:

`ros2_bridge/esp32_camera_bridge`

The package connects to an ESP32 camera MJPEG stream and publishes ROS 2 images.

## What it does

1. Connects to `http://<esp32-ip>/stream`.
2. Reads MJPEG multipart data and extracts JPEG frames.
3. Decodes each frame with OpenCV.
4. Publishes frames as `sensor_msgs/msg/Image` on `/esp32/camera/image_raw`.

## Where to set the stream IP

Preferred way: pass it at runtime using launch/CLI parameters.

Default value locations:

- `ros2_bridge/esp32_camera_bridge/esp32_camera_bridge/mjpeg_image_publisher.py`
  - `self.declare_parameter('stream_url', 'http://192.168.1.100/stream')`
- `ros2_bridge/esp32_camera_bridge/launch/esp32_camera_bridge.launch.py`
  - `default_value='http://192.168.1.100/stream'`

## Project structure

- `esp32_camera_bridge/`: Main Python node code (`mjpeg_image_publisher.py`).
- `launch/`: Launch file definitions (`esp32_camera_bridge.launch.py`) for
  running the node with parameters.
- `package.xml`, `setup.py`, `setup.cfg`: ROS 2 package metadata and Python
  packaging.

## How to run locally (development)

Prerequisites:

1. ROS 2 Humble installed.
2. `colcon` installed.
3. ESP32 reachable on the same network.

Put package into a workspace:

```bash
mkdir -p ~/ros2_ws/src
cp -r <repo>/ros2_bridge/esp32_camera_bridge ~/ros2_ws/src/
```

Build:

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select esp32_camera_bridge
source install/setup.bash
```

Run (recommended: launch file):

```bash
ros2 launch esp32_camera_bridge esp32_camera_bridge.launch.py stream_url:=http://<esp32-ip>/stream
```

Run (direct node):

```bash
ros2 run esp32_camera_bridge mjpeg_image_publisher --ros-args -p stream_url:=http://<esp32-ip>/stream
```

## How to test quickly

1. Check raw stream is reachable:
   - `curl http://<esp32-ip>/stream`
2. Start the bridge node.
3. Verify topic exists:
   - `ros2 topic list | grep esp32/camera/image_raw`
4. Verify one message arrives:
   - `ros2 topic echo /esp32/camera/image_raw --once`

## How to deploy

For deployment to another machine/robot:

1. Install ROS 2 Humble and runtime dependencies on target.
2. Copy repository (or just package folder) to target.
3. Build in a ROS 2 workspace (`colcon build`).
4. Run with a fixed launch command or startup service.

Typical deployment options:

- Manual launch: Run `ros2 launch ...` after sourcing workspace.
- System service (recommended for auto-start): Create a `systemd` service that
  sources ROS 2 + workspace and runs the launch command.
- Containerized run: Build a Docker image with ROS 2 + this package and run it
  with host networking.

## Notes

- The package build was validated in ROS 2 Humble.
- Runtime success depends on network access to the ESP32 stream URL.
