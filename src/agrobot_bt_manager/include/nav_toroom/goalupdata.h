#pragma once

#include <behaviortree_cpp_v3/condition_node.h>
#include <string>
#include <mutex>
#include <ros/ros.h>

class GoalUpdateCondition : public BT::ConditionNode
{
public:
    GoalUpdateCondition(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ConditionNode(name, config)
    {}

    static BT::PortsList providedPorts()
    {
        return { BT::InputPort<std::string>("nav_target_room") };
    }

    BT::NodeStatus tick() override
    {
        std::string current_target;
        if (!getInput("nav_target_room", current_target))
        {
            ROS_WARN("GoalUpdateCondition: failed to get nav_target_room input");
            return BT::NodeStatus::FAILURE;
        }

        std::lock_guard<std::mutex> lock(mutex_);
        if (current_target != last_target_)
        {
            ROS_INFO("GoalUpdateCondition: target changed from [%s] to [%s]",
                     last_target_.c_str(), current_target.c_str());
            last_target_ = current_target;
            return BT::NodeStatus::SUCCESS;
        }

        return BT::NodeStatus::FAILURE;
    }

private:
    std::string last_target_;
    std::mutex mutex_;
};
