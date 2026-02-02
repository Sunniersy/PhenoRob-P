#ifndef OPEN_DOOR_ACTION_H
#define OPEN_DOOR_ACTION_H

#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>

class OpenDoorAction : public BT::SyncActionNode
{
public:
    OpenDoorAction(const std::string& name, const BT::NodeConfiguration& config);

    static BT::PortsList providedPorts();

    virtual BT::NodeStatus tick() override;

private:
    ros::NodeHandle nh_;
    ros::Publisher door_cmd_pub_;
};

#endif // OPEN_DOOR_ACTION_H
