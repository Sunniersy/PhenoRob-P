#pragma once

#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>

class AlwaysRunning : public BT::StatefulActionNode
{
public:
    AlwaysRunning(const std::string& name, const BT::NodeConfiguration& config)
        : BT::StatefulActionNode(name, config) {}

    static BT::PortsList providedPorts()
    {
        return {};
    }

    BT::NodeStatus onStart() override
    {
        ROS_INFO("AlwaysRunning started.");
        return BT::NodeStatus::RUNNING;
    }

    BT::NodeStatus onRunning() override
    {
        ROS_INFO_ONCE("AlwaysRunning still running...");
        return BT::NodeStatus::RUNNING;
    }

    void onHalted() override
    {
        ROS_WARN("AlwaysRunning was halted.");
    }
};
