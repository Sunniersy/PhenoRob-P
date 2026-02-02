#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

'''
parameters=[
        {'device_model': 'MS500'},
        {'frame_id': 'laser_frame'},
        {'cloud_topic': 'point_cloud'},
        {'lidar_ip': '192.168.1.100'},
        {'lidar_port': 2007},
        {'angle_min': -135.0},
        {'angle_max': 135.0},
        {'range_min': 0.05},
        {'range_max': 30.0},
        {'inverted': False},
        {'motor_speed': 15},
        {'filter_size': 1},
        {'motor_dir': 0}
      ]
'''

def generate_launch_description():
  # LiDAR publisher node
  ordlidar_node = Node(
      package='oradar_ros',
      node_executable='oradar_pointcloud',
      node_name='MS500',
      output='screen',
      parameters=[
        {'device_model': 'MS500'},
        {'frame_id': 'laser_frame'},
        {'cloud_topic': 'point_cloud'},
        {'lidar_ip': '192.168.1.100'},
        {'lidar_port': 2007},
        {'angle_min': -135.0},
        {'angle_max': 135.0},
        {'range_min': 0.05},
        {'range_max': 30.0},
        {'inverted': False},
        {'motor_speed': 15},
        {'filter_size': 1},
        {'motor_dir': 0}
      ]
  )

  # base_link to laser_frame tf node
  base_link_to_laser_tf_node = Node(
    package='tf2_ros',
    node_executable='static_transform_publisher',
    node_name='base_link_to_base_laser',
    arguments=['0','0','0.18','0','0','0','base_link','laser_frame']
  )


  # Define LaunchDescription variable
  ord = LaunchDescription()

  ord.add_action(ordlidar_node)
  #ord.add_action(base_link_to_laser_tf_node)

  return ord