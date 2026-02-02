#include "task_handler/wait_attarget_pose.h"

WaitAtTargetPose::WaitAtTargetPose(const std::string& name, const BT::NodeConfiguration& config)
    : BT::AsyncActionNode(name, config), halt_requested_(false)
{
}

BT::NodeStatus WaitAtTargetPose::tick()
{
    ROS_INFO("WaitAtTargetPose: started waiting.");
    halt_requested_ = false;

    ros::Rate rate(10); // 10 Hz check rate

    while (ros::ok() && !halt_requested_)
    {
        // 你可以在这里监听某种停止等待的信号（例如新命令、事件触发等）

        rate.sleep();
    }

    if (halt_requested_)
    {
        ROS_WARN("WaitAtTargetPose: interrupted.");
        return BT::NodeStatus::SUCCESS;
    }

    ROS_INFO("WaitAtTargetPose: completed.");
    return BT::NodeStatus::SUCCESS;
}

void WaitAtTargetPose::halt()
{
    ROS_WARN("WaitAtTargetPose: halt() called.");
    halt_requested_ = true;
}
