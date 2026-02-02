#pragma once

#include <behaviortree_cpp_v3/condition_node.h>
#include <ros/ros.h>
#include <tf2_ros/transform_listener.h>
#include <geometry_msgs/TransformStamped.h>
#include <agrobot_bt_manager/get_roompose.h>
#include <cmath>

class AtTargetRoomCondition : public BT::ConditionNode {
public:
  AtTargetRoomCondition(const std::string& name, const BT::NodeConfiguration& config);

  static BT::PortsList providedPorts();
    
  BT::NodeStatus tick() override;

private:
  ros::NodeHandle nh_;
  ros::ServiceClient get_room_pose_client_;
  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
  std::string last_room_name_;
};
