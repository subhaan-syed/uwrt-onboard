from setuptools import setup

package_name = 'turtle_magic'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Subhaan Syed',
    maintainer_email='subhaan.syed01@gmail.com',
    description='A ROS2 node that drives the turtle along a defined path when triggered by a service call.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'path_drawer = turtle_magic.path_drawer:main',
        ],
    },
)
