#pragma once

#include <behaviortree_cpp_v3/condition_node.h>
#include <ros/ros.h>
#include <agrobot_bt_manager/voice_command.h>
#include <mutex>

class WaitForNewCommandCondition : public BT::ConditionNode
{
public:
    WaitForNewCommandCondition(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ConditionNode(name, config), nh_("~"), new_command_available_(false)
    {
        sub_ = nh_.subscribe("/voice_command", 10, &WaitForNewCommandCondition::voiceCommandCallback, this);
        app_sub_ = nh_.subscribe("/app_command",10,&WaitForNewCommandCondition::appCommandCallback,this);
    }

    static BT::PortsList providedPorts()
    {
        return {
            BT::OutputPort<std::string>("nav_target_room"),  // 输出到黑板
            BT::OutputPort<std::string>("voice_task_command"),
            BT::InputPort<bool>("task_locked")
        };  
    }

    BT::NodeStatus tick() override
    {
        bool task_locked = false;
        getInput("task_locked", task_locked);

        std::lock_guard<std::mutex> lock(mutex_);
        
        // ROS_INFO("WaitForNewCommandCondition::tick() called. new_command_available_=%s",
            //  new_command_available_ ? "true" : "false");
        if (new_command_available_)
        { 
            if(last_room_name_!= current_room_name_||last_task_command_!=current_task_command_){
                if(task_locked)
                {
                    ROS_WARN_THROTTLE(5.0, "Task is locked, ignoring new command.");
                    last_room_name_ = current_room_name_;
                    last_task_command_ = current_task_command_;
                    new_command_available_ = false; 
                    return BT::NodeStatus::FAILURE;
                }
                else
                {
                    setOutput("nav_target_room", current_room_name_);
                    setOutput("voice_task_command",current_task_command_);
                    ROS_INFO("New room command available, proceeding to GoToRoomAction");
                    last_room_name_ = current_room_name_;
                    last_task_command_ = current_task_command_;
                    new_command_available_ = false; 
                    return BT::NodeStatus::SUCCESS;
                }
            }
            else
            {
                last_room_name_ = current_room_name_;
                last_task_command_ = current_task_command_;
                new_command_available_ = false; 
                ROS_WARN_THROTTLE(5.0, "received same command.");
                return BT::NodeStatus::FAILURE;
            }
        }
        
        return BT::NodeStatus::FAILURE;
    }

private:
    // =========语音命令接收===============
    void voiceCommandCallback(const agrobot_bt_manager::voice_command::ConstPtr& msg)
    {
        std::lock_guard<std::mutex> lock(mutex_);
        current_room_name_ = msg->room_name;
        current_task_command_ = msg->task_command;
        new_command_available_ = true;
    }
    // ==========app命令接收================
    void appCommandCallback(const agrobot_bt_manager::voice_command::ConstPtr& msg)
    {

        std::lock_guard<std::mutex> lock(mutex_);
        current_room_name_ = msg->room_name;
        current_task_command_ = msg->task_command;
        new_command_available_ = true;
        
    }

    ros::NodeHandle nh_;
    ros::Subscriber sub_;
    ros::Subscriber app_sub_;
    bool new_command_available_;
    std::string last_room_name_;
    std::string last_task_command_;
    std::string current_room_name_;
    std::string current_task_command_;
    std::mutex mutex_;
};
