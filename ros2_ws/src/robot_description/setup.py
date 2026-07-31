import os
from glob import glob
from setuptools import setup, find_packages

package_name = 'robot_description'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # launch
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),

        # URDF / xacro
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*')),

        # swiaty Gazebo
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.world')),

        # konfiguracje RViz2
        (os.path.join('share', package_name, 'rviz'),
            glob('rviz/*.rviz')),

        # pliki YAML (nav2, slam_toolbox, kontrolery)
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),

        # meshe (jesli sa)
        (os.path.join('share', package_name, 'meshes'),
            glob('meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Grzegorz',
    maintainer_email='grzegorz@todo.todo',
    description='Opis URDF i symulacja Gazebo robota SNIFF',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)