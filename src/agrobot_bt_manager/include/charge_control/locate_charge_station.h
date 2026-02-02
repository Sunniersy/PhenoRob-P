#pragma once

#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>
#include <std_msgs/Bool.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>

class LocateChargingStation : public BT::AsyncActionNode
{
public:
    LocateChargingStation(const std::string& name, const BT::NodeConfiguration& config);

    static BT::PortsList providedPorts();

    BT::NodeStatus tick() override;

private:
    ros::NodeHandle nh_;
    ros::Publisher pub_;
    tf2_ros::Buffer tf_buffer_;
    tf2_ros::TransformListener tf_listener_;

    bool thread_started_ = false;
};
