#include "charge_control/locate_charge_station.h"
#include <geometry_msgs/TransformStamped.h>
#include <tf2/exceptions.h>

LocateChargingStation::LocateChargingStation(const std::string& name, const BT::NodeConfiguration& config)
: BT::AsyncActionNode(name, config), tf_listener_(tf_buffer_)
{
    pub_ = nh_.advertise<std_msgs::Bool>("/charging_task_active", 1, true);
}

BT::PortsList LocateChargingStation::providedPorts()
{
    return {};
}

BT::NodeStatus LocateChargingStation::tick()
{
    // 新开线程去检测tf
    if (!thread_started_)
    {
        thread_started_ = true;

        // 发布启动信号（只发一次）
        std_msgs::Bool msg;
        msg.data = true;
        pub_.publish(msg);
        ROS_INFO("publish charging_task_active...");
    
        std::thread([this]() {
            ros::Rate rate(10);
            while (ros::ok())
            {
                try
                {
                    auto tf = tf_buffer_.lookupTransform("result", "base_link", ros::Time(0));
                    ROS_INFO("LocateChargingStation: tf result detected");
                    this->setStatus(BT::NodeStatus::SUCCESS);
                    return;
                }
                catch (tf2::TransformException& ex)
                {
                    ROS_INFO_THROTTLE(1.0, "LocateChargingStation: waiting for tf result...");
                }
                rate.sleep();
            }
            this->setStatus(BT::NodeStatus::FAILURE);
        }).detach();
    }

    return BT::NodeStatus::RUNNING;  // 立即返回，表示正在运行
}

