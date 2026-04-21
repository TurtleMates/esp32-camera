from glob import glob

from setuptools import find_packages, setup

package_name = 'esp32_camera_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mounir',
    maintainer_email='mm_mostefai@esi.dz',
    description='Bridge an ESP32 MJPEG camera stream into a ROS 2 topic.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mjpeg_image_publisher = esp32_camera_bridge.mjpeg_image_publisher:main',
        ],
    },
)