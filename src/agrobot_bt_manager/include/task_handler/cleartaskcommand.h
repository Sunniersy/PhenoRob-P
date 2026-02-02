#pragma once

#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>

class ClearTaskCommandNode : public BT::SyncActionNode
{
public:
    ClearTaskCommandNode(const std::string& name, const BT::NodeConfiguration& config)
        : BT::SyncActionNode(name, config) {}

    static BT::PortsList providedPorts()
    {
        return {
            BT::OutputPort<std::string>("voice_task_command"),
            BT::OutputPort<std::string>("nav_target_room")
        };
    }

    BT::NodeStatus tick() override
    {
        ROS_INFO("ClearTaskCommandNode: Clearing voice_task_command and nav_target_room");
        setOutput("voice_task_command", "IDEL");
        setOutput("nav_target_room", "");
        return BT::NodeStatus::SUCCESS;
    }
};
