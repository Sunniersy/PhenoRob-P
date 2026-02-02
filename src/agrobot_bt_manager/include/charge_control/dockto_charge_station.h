// charge_control/dockto_charge_station.h
#ifndef DOCKTO_CHARGE_STATION_H
#define DOCKTO_CHARGE_STATION_H

#include <behaviortree_cpp_v3/bt_factory.h>
#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <pattern_matcher/icpchargeAction.h> 
#include "RobotCar/carinfo.h"
#include <std_msgs/Bool.h>
using namespace BT;

class DockToChargingStation : public StatefulActionNode
{
public:
    DockToChargingStation(const std::string& name, const NodeConfiguration& config)
        : StatefulActionNode(name, config),
          charge_client_("icp_charge_action", true) // 动作名称
    {
        ros::NodeHandle nh;
        ROS_INFO("Waiting for charging action server...");
        charge_client_.waitForServer();
        ROS_INFO("Charging action server ready!");
        battery_sub = nh.subscribe("/CarInfo", 1, &DockToChargingStation::batteryCallback, this);
        pub_ = nh.advertise<std_msgs::Bool>("/charging_task_active", 1, true);
    }

    static PortsList providedPorts()
    {
        return {
            BT::OutputPort<bool>("IsCharging")
        };
    }

    NodeStatus onStart() override
    {
        halt_requested_ = false;

        std_msgs::Bool msg;
        msg.data = true;
        pub_.publish(msg);//允许对接
        
        // 发送充电启动请求
        pattern_matcher::icpchargeGoal goal;
        goal.charge_enable = true;
        goal.charge_stop= false;
        
        charge_client_.sendGoal(goal,
                               boost::bind(&DockToChargingStation::activeCallback, this));
                               
        
        ROS_INFO("Starting charging process...");
        return NodeStatus::RUNNING;
    }

    NodeStatus onRunning() override
    {
        if(halt_requested_)
        {
            return NodeStatus::FAILURE;
        }
        
        // 检查动作状态
        auto state = charge_client_.getState();
        
        if (state == actionlib::SimpleClientGoalState::SUCCEEDED) {
            ROS_INFO("Charging completed successfully");
            setOutput("IsCharging", true);//正在充电
            return NodeStatus::SUCCESS;
        }
        else if (state == actionlib::SimpleClientGoalState::ACTIVE) {
            return NodeStatus::RUNNING;
        }
        else if (state == actionlib::SimpleClientGoalState::ABORTED) {
            ROS_ERROR("Charging process aborted");
            std_msgs::Bool msg;
            msg.data = false;
            pub_.publish(msg);
            
            return NodeStatus::FAILURE;
        }
        else {
            return NodeStatus::RUNNING;
        }

        
    }

    void onHalted() override
    {
        std_msgs::Bool msg;
        msg.data = false;
        pub_.publish(msg);

        halt_requested_ = true;
        
        charge_client_.cancelGoal();  // 取消充电

        ROS_WARN("Charging onhalted");
    }

    void batteryCallback(const RobotCar::carinfo& car)
    {
        std::lock_guard<std::mutex> lock(battery_mutex_);
        current_battery_level_ = car.power;
    }

private:
    // 动作服务器回调函数
    void activeCallback()
    {
        ROS_INFO("Charging process activated");
    }

    actionlib::SimpleActionClient<pattern_matcher::icpchargeAction> charge_client_;
    ros::Subscriber battery_sub;
    ros::Publisher pub_;
    std::mutex battery_mutex_;
    double min_battery_level_ = 99;
    double current_battery_level_ = 0.0;
    bool halt_requested_ = false;

    // 后退等待逻辑相关
    ros::Time halt_start_time_;
    bool halt_waiting_ = false;
    double halt_wait_duration_ = 5.0; // 后退持续时间（单位：秒）
};

#endif 