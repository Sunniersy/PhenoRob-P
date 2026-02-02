#include "opendoor/open_door_action.h"
#include <std_msgs/Bool.h>
#include <chrono>
#include <thread>

OpenDoorAction::OpenDoorAction(const std::string& name, const BT::NodeConfiguration& config)
    : BT::SyncActionNode(name, config)
{
    // 假设有一个话题 "door_command" 可以控制门的开关
    door_cmd_pub_ = nh_.advertise<std_msgs::Bool>("/door_command", 1);
}

BT::PortsList OpenDoorAction::providedPorts()
{
    return {
        BT::InputPort<bool>("Door_open_cmd")
    };  // 如果未来要指定哪扇门，可以添加 InputPort<string>("door_id")
}

BT::NodeStatus OpenDoorAction::tick()
{
    ROS_INFO("OpenDoorAction: sending open door command");

    
    std_msgs::Bool msg;
    msg.data = true;
    door_cmd_pub_.publish(msg);

    // 模拟开门动作耗时
    std::this_thread::sleep_for(std::chrono::seconds(2));

    ROS_INFO("OpenDoorAction: door should be open now");
    return BT::NodeStatus::SUCCESS;
}
