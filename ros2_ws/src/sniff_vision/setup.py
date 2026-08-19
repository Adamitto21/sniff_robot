from setuptools import setup
import os
from glob import glob

package_name = 'sniff_vision'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'models'), glob('models/*.blob')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'oak_detector = sniff_vision.oak_detector_node:main',
	    'oak_detector_hq = sniff_vision.oak_detector_hq_node:main',
            'web_viewer = sniff_vision.web_viewer_node:main',
            'video_recorder = sniff_vision.video_recorder_node:main',
        ],
    },
)
