#!/usr/bin/env python3

import threading
import time

import cv2
import numpy as np
import requests
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

JPEG_START = b'\xff\xd8'
JPEG_END = b'\xff\xd9'


class MjpegImagePublisher(Node):
    def __init__(self):
        super().__init__('esp32_mjpeg_image_publisher')

        self.declare_parameter('stream_url', 'http://192.168.1.100/stream')
        self.declare_parameter('topic', '/esp32/camera/image_raw')
        self.declare_parameter('frame_id', 'esp32_camera')
        self.declare_parameter('queue_size', 10)
        self.declare_parameter('chunk_size', 4096)
        self.declare_parameter('reconnect_delay', 2.0)
        self.declare_parameter('request_timeout', 30.0)
        self.declare_parameter('flip_horizontal', False)
        self.declare_parameter('flip_vertical', False)

        topic = self.get_parameter('topic').value
        queue_size = int(self.get_parameter('queue_size').value)
        self._frame_id = self.get_parameter('frame_id').value
        self._chunk_size = int(self.get_parameter('chunk_size').value)
        self._reconnect_delay = float(self.get_parameter('reconnect_delay').value)
        self._request_timeout = float(self.get_parameter('request_timeout').value)
        self._flip_horizontal = bool(self.get_parameter('flip_horizontal').value)
        self._flip_vertical = bool(self.get_parameter('flip_vertical').value)

        self._bridge = CvBridge()
        self._publisher = self.create_publisher(Image, topic, queue_size)
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._stream_loop, daemon=True)
        self._worker.start()

        stream_url = self.get_parameter('stream_url').value
        self.get_logger().info(f'Publishing frames from {stream_url} to {topic}')

    def destroy_node(self):
        self._stop_event.set()
        if self._worker.is_alive():
            self._worker.join(timeout=2.0)
        super().destroy_node()

    def _stream_loop(self):
        while rclpy.ok() and not self._stop_event.is_set():
            stream_url = self.get_parameter('stream_url').value
            try:
                self._consume_stream(stream_url)
            except requests.RequestException as exc:
                if self._stop_event.is_set() or not rclpy.ok():
                    break
                self.get_logger().warn(f'Stream connection problem: {exc}')
                time.sleep(self._reconnect_delay)
            except Exception as exc:
                if self._stop_event.is_set() or not rclpy.ok():
                    break
                self.get_logger().error(f'Unexpected stream error: {exc}')
                time.sleep(self._reconnect_delay)

    def _consume_stream(self, stream_url):
        with requests.get(
            stream_url,
            stream=True,
            timeout=(5.0, self._request_timeout),
        ) as response:
            response.raise_for_status()
            buffer = bytearray()
            for chunk in response.iter_content(chunk_size=self._chunk_size):
                if self._stop_event.is_set() or not rclpy.ok():
                    return
                if not chunk:
                    continue

                buffer.extend(chunk)
                self._extract_and_publish_frames(buffer)

    def _extract_and_publish_frames(self, buffer):
        while True:
            start = buffer.find(JPEG_START)
            if start == -1:
                if len(buffer) > self._chunk_size * 2:
                    del buffer[:-2]
                return

            end = buffer.find(JPEG_END, start + 2)
            if end == -1:
                if start > 0:
                    del buffer[:start]
                return

            frame_bytes = bytes(buffer[start:end + 2])
            del buffer[:end + 2]
            self._publish_frame(frame_bytes)

    def _publish_frame(self, frame_bytes):
        np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)
        image = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
        if image is None:
            self.get_logger().warn('Dropped one JPEG frame that could not be decoded.')
            return

        if self._flip_horizontal:
            image = cv2.flip(image, 1)
        if self._flip_vertical:
            image = cv2.flip(image, 0)

        msg = self._bridge.cv2_to_imgmsg(image, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        self._publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MjpegImagePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()