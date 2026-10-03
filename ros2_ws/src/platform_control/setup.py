import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'platform_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='adam.lamecki04@gmail.com',
    description='Paczka do testowania platformy',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'platform_driver = platform_control.platform_driver:main',
            'keyboard = platform_control.keyboard:main',
            'odometry = platform_control.platform_brain:main',
            'patrol = platform_control.patrol_node:main'
        ],
    },
)
