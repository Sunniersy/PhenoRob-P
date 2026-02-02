#pragma once

#include <behaviortree_cpp_v3/condition_node.h>
#include <ros/ros.h>
#include <tf2_ros/transform_listener.h>
#include <geometry_msgs/TransformStamped.h>
#include <agrobot_bt_manager/get_roompose.h>

class CheckIfNeedOpenDoor : public BT::ConditionNode
{
public:
    CheckIfNeedOpenDoor(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ConditionNode(name, config), tf_listener_(tf_buffer_)
    {
        ros::NodeHandle nh;
        room_pose_client_ = nh.serviceClient<agrobot_bt_manager::get_roompose>("/get_room_pose");
    }

    static BT::PortsList providedPorts()
    {
        return {
            BT::InputPort<std::string>("nav_target_room"),
            BT::InputPort<double>("door_y", -4.5, "Y coordinate of the door"),
            BT::OutputPort<std::string>("target_door")
        };
    }

    BT::NodeStatus tick() override
    {
        std::string nav_target_room;
        if (!getInput("nav_target_room", nav_target_room))
        {
            ROS_ERROR("[MoveBaseToRoom] Missing input: nav_target_room");
            return BT::NodeStatus::FAILURE;
        }

        if(last_nav_target_room_ == nav_target_room)
        {
            return BT::NodeStatus::FAILURE;//房间没更新，直接不判断
        }

        last_nav_target_room_ = nav_target_room;

        // 1. 调用服务获取目标房间坐标
        agrobot_bt_manager::get_roompose srv;
        srv.request.room_name = nav_target_room;
        if (!room_pose_client_.call(srv) || !srv.response.success)
        {
            ROS_ERROR_STREAM_THROTTLE(2.0, "CheckIfNeedOpenDoor: Failed to get room pose for [" << nav_target_room << "]");
            return BT::NodeStatus::FAILURE;
        }
        double target_y = srv.response.y;

        // 2. 获取机器人当前位姿
        geometry_msgs::TransformStamped transform;
        try
        {
            transform = tf_buffer_.lookupTransform("map", "base_link", ros::Time(0), ros::Duration(0.5));
        }
        catch (tf2::TransformException& ex)
        {
            ROS_WARN_STREAM_THROTTLE(5.0, "CheckIfNeedOpenDoor TF Error: " << ex.what());
            return BT::NodeStatus::FAILURE;
        }

        double robot_y = transform.transform.translation.y;

        // 3. 判断门是否在两者之间
        double door_y = -4.5;
        getInput("door_y", door_y);

        bool need_open = ((robot_y < door_y && target_y > door_y) ||
                          (robot_y > door_y && target_y < door_y));

        if (need_open)//需要开门就判断是去门的哪边
        {
            std::string door_target = (robot_y > door_y) ? "door_a" : "door_b";
            // ROS_INFO_STREAM("Robot y=" << robot_y << ", door_y=" << door_y
            //                 << ". Navigating to " << door_target);
            setOutput("target_door",door_target);

            ROS_INFO("CheckIfNeedOpenDoor: Door is between robot and target room SO need to open door");
            return BT::NodeStatus::SUCCESS;
        }
        else
        {
            ROS_INFO("CheckIfNeedOpenDoor: No need to open door");
            return BT::NodeStatus::FAILURE;
        }
    }

private:
    ros::ServiceClient room_pose_client_;
    tf2_ros::Buffer tf_buffer_;
    tf2_ros::TransformListener tf_listener_;
    std::string last_nav_target_room_;
};
