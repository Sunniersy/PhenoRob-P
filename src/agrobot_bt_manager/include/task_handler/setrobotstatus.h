#pragma once

#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>
#include <agrobot_bt_manager/robot_status.h>

class SetRobotStatusNode : public BT::SyncActionNode
{
public:
    SetRobotStatusNode(const std::string& name, const BT::NodeConfiguration& config);

    static BT::PortsList providedPorts()
    {
        return {
            BT::InputPort<std::string>("status"),
            BT::OutputPort<std::string>("current_status")
        };
    }

    BT::NodeStatus tick() override;

private:
    ros::NodeHandle nh_;
    ros::Publisher status_pub_;
    std::string last_status_;
};
