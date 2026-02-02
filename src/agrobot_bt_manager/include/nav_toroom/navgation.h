// nav_toroom/movebase_to_room.h
#ifndef MOVEBASE_TO_ROOM_H
#define MOVEBASE_TO_ROOM_H

#include <behaviortree_cpp_v3/bt_factory.h>
#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <move_base_msgs/MoveBaseAction.h>
#include <agrobot_bt_manager/get_roompose.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <tf2_ros/transform_listener.h>
#include <tf/tf.h>
#include "agrobot_bt_manager/arrived_point.h"

using namespace BT;

class MoveBaseToRoom : public StatefulActionNode
{
public:
    MoveBaseToRoom(const std::string& name, const NodeConfiguration& config)
        : StatefulActionNode(name, config),
          move_base_client_("move_base", true)
    {
        ros::NodeHandle nh;
        room_pose_client_ = nh.serviceClient<agrobot_bt_manager::get_roompose>("get_room_pose");
        ROS_INFO("Waiting for services...");
        room_pose_client_.waitForExistence();
        move_base_client_.waitForServer();
        ROS_INFO("Services ready!");
        pub_ = nh.advertise<agrobot_bt_manager::arrived_point>("/arrived_point", 10);
    }

    static PortsList providedPorts()
    {
        return { InputPort<std::string>("nav_target_room") };
    }

    NodeStatus onStart() override
    {
        // 从黑板获取房间名称
        if (!getInput<std::string>("nav_target_room", target_room_)) {
            ROS_ERROR("[MoveBaseToRoom] Missing input: nav_target_room");
            return NodeStatus::FAILURE;
        }

            // 检查目标是否改变
        if (target_room_ == current_target_room_) {
            if(is_active_){
                return NodeStatus::RUNNING;
            }
            else
                return NodeStatus::SUCCESS;
                
        }

        // 如果正在导航且目标改变，取消当前导航
        if (is_active_) {
            move_base_client_.cancelGoal();
            is_active_ = false;
            ros::Duration(0.1).sleep();
        }

        // 调用查询房间坐标服务
        agrobot_bt_manager::get_roompose srv;
        srv.request.room_name = target_room_;

        if (!room_pose_client_.call(srv)) {
            ROS_ERROR("Failed to call service get_room_pose");
            return NodeStatus::FAILURE;
        }

        if (!srv.response.success) {
            ROS_ERROR("Service returned error: %s", srv.response.message.c_str());
            return NodeStatus::FAILURE;
        }

        // 设置导航目标
        move_base_msgs::MoveBaseGoal goal;
        goal.target_pose.header.frame_id = "map";
        goal.target_pose.header.stamp = ros::Time::now();
        goal.target_pose.pose.position.x = srv.response.x;
        goal.target_pose.pose.position.y = srv.response.y;
        goal.target_pose.pose.orientation = 
        tf::createQuaternionMsgFromYaw(srv.response.yaw);

         // 更新当前目标状态
        current_target_room_ = target_room_;
        is_active_ = true;

        // 发送导航目标
        move_base_client_.sendGoal(goal);
        ROS_INFO("Sending navigation goal to %s: (%.2f, %.2f, %.2f)", 
                target_room_.c_str(), srv.response.x, srv.response.y, srv.response.yaw);
        return NodeStatus::RUNNING;
    }

    NodeStatus onRunning() override
    {
        auto state = move_base_client_.getState();
        
        if (state == actionlib::SimpleClientGoalState::SUCCEEDED) {
            ROS_INFO("Navigation to %s succeeded!", target_room_.c_str());
            is_active_ = false;
            
            agrobot_bt_manager::arrived_point msg;
            msg.room_name = target_room_;
            msg.arrived = true;
            pub_.publish(msg);
            
            return NodeStatus::SUCCESS;
            
        }
        else if (state == actionlib::SimpleClientGoalState::ACTIVE) {
            return NodeStatus::RUNNING;
        }
        else if(state == actionlib::SimpleClientGoalState::ABORTED){
            is_active_ = false;
            return NodeStatus::FAILURE;
        }
        else
        {
            return NodeStatus::RUNNING;
        }
    }

    void onHalted() override
    {
        ROS_WARN("Navigation interrupted, canceling goal");
        move_base_client_.cancelGoal();
        is_active_ = false;
    }

private:
    ros::ServiceClient room_pose_client_;
    actionlib::SimpleActionClient<move_base_msgs::MoveBaseAction> move_base_client_;
    std::string target_room_;
    std::string current_target_room_;
    bool is_active_ = false;
    ros::Publisher pub_;
};

#endif