#ifndef STOP_CAHRGE_ACTION_H
#define STOP_CAHRGE_ACTION_H

#include <behaviortree_cpp_v3/action_node.h>
#include <actionlib/client/simple_action_client.h>
#include <pattern_matcher/icpchargeAction.h> 
#include <std_msgs/Bool.h>

class StopChargingAction : public BT::SyncActionNode {
public:
    StopChargingAction(const std::string& name, const BT::NodeConfiguration& config)
        : SyncActionNode(name, config), ac_("/icp_charge_action", true) {
            ros::NodeHandle nh;
            pub_ = nh.advertise<std_msgs::Bool>("/charging_task_active", 1, true);
        }

    static BT::PortsList providedPorts() {
        return {
            BT::InputPort<bool>("IsCharging"),
            BT::OutputPort<bool>("IsCharging")
        };
    }

    BT::NodeStatus tick() override {
        if (!ac_.waitForServer(ros::Duration(1.0))) {
            ROS_ERROR("StopChargingAction: Action server not available");
            return BT::NodeStatus::FAILURE;
        }

        std_msgs::Bool msg;
        msg.data = false;
        pub_.publish(msg);

        pattern_matcher::icpchargeGoal goal;
        goal.charge_stop = true;

        ac_.sendGoal(goal);
        ac_.waitForResult(ros::Duration(8.0));

        if (ac_.getState() == actionlib::SimpleClientGoalState::SUCCEEDED) {
            ROS_INFO("StopChargingAction succeeded.");
            setOutput("IsCharging", false);
            return BT::NodeStatus::SUCCESS;
        } else {
            ROS_WARN("StopChargingAction failed.");
            return BT::NodeStatus::FAILURE;
        }
        
    }

private:
    actionlib::SimpleActionClient<pattern_matcher::icpchargeAction> ac_;
    ros::Publisher pub_;
};

#endif