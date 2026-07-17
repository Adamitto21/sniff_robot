from setuptools import find_packages
from setuptools import setup

setup(
    name='sniff_msgs',
    version='0.0.1',
    packages=find_packages(
        include=('sniff_msgs', 'sniff_msgs.*')),
)
