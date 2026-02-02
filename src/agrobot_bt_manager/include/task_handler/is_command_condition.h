#pragma once
#include <behaviortree_cpp_v3/condition_node.h>

class IsCommand : public BT::ConditionNode {
public:
  IsCommand(const std::string& name, const BT::NodeConfiguration& config)
    : BT::ConditionNode(name, config) {}

  static BT::PortsList providedPorts() {
    return {
      BT::InputPort<std::string>("voice_task_command"),
      BT::InputPort<std::string>("task_type")  // 要匹配的任务类型
    };
  }

  BT::NodeStatus tick() override {
    std::string cmd, type;
    if (!getInput("voice_task_command", cmd) || !getInput("task_type", type)) {
      return BT::NodeStatus::FAILURE;
    }
     ROS_INFO_STREAM("[Blackboard] voice_task_command = [" << cmd << "]");
    return (cmd == type) ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
  }
};
