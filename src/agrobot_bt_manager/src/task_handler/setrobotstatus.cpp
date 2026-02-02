#include "task_handler/setrobotstatus.h"

SetRobotStatusNode::SetRobotStatusNode(const std::string& name, const BT::NodeConfiguration& config)
    : BT::SyncActionNode(name, config), nh_("~"), last_status_("")
{
    status_pub_ = nh_.advertise<agrobot_bt_manager::robot_status>("/robot_status", 10);
}

BT::NodeStatus SetRobotStatusNode::tick()
{
    std::string status;
    if (!getInput("status", status))
    {
        throw BT::RuntimeError("Missing input [status]");
    }

    setOutput("current_status", status);

    // 如果状态未变化，则不发布
    if (status == last_status_)
    {
        return BT::NodeStatus::SUCCESS;
    }

    // 构造消息
    agrobot_bt_manager::robot_status msg;
    msg.header.stamp = ros::Time::now();
    msg.header.frame_id = "base_link";
    msg.status = status;

    // 发布
    status_pub_.publish(msg);
    ROS_INFO_STREAM("Robot status updated and published: " << status);

    last_status_ = status;
    return BT::NodeStatus::SUCCESS;
}
