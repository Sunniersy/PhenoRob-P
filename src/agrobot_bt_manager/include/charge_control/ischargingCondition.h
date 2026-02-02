#ifndef IS_CHARGING_CONDITION_H
#define IS_CHARGING_CONDITION_H

#include <ros/ros.h>
#include <behaviortree_cpp_v3/condition_node.h>

class IsChargingCondition : public BT::ConditionNode {
public:
    IsChargingCondition(const std::string& name, const BT::NodeConfiguration& config)
        : ConditionNode(name, config) {}

    static BT::PortsList providedPorts() {
        return { BT::InputPort<bool>("IsCharging") };
    }

    BT::NodeStatus tick() override {
        bool charging = false;
        if (getInput("IsCharging", charging)) {
            return charging ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
        }
        return BT::NodeStatus::FAILURE;
    }
};

#endif