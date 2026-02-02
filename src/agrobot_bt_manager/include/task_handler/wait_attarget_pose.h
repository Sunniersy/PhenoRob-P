#pragma once

#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>

class WaitAtTargetPose : public BT::AsyncActionNode
{
public:
    WaitAtTargetPose(const std::string& name, const BT::NodeConfiguration& config);

    static BT::PortsList providedPorts()
    {
        return {};
    }

    BT::NodeStatus tick() override;
    void halt() override;

private:
    bool halt_requested_;
};
