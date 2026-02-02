#pragma once

#include <behaviortree_cpp_v3/action_node.h> // 改为继承自ActionNode
#include <ros/ros.h>
#include <agrobot_bt_manager/voice_command.h>
#include <mutex>
#include <atomic>

class AsyncCommandListener : public BT::StatefulActionNode
{
public:
    AsyncCommandListener(const std::string& name, const BT::NodeConfiguration& config)
        : BT::StatefulActionNode(name, config), nh_("~")
    {
        sub_ = nh_.subscribe("/voice_command", 10, &AsyncCommandListener::voiceCommandCallback, this);
        app_sub_ = nh_.subscribe("/app_command", 10, &AsyncCommandListener::appCommandCallback, this);
    }

    static BT::PortsList providedPorts()
    {
        return {
            BT::OutputPort<std::string>("nav_target_room"),
            BT::OutputPort<std::string>("voice_task_command"),
            BT::InputPort<bool>("task_locked")
        };  
    }

    // 节点开始执行时调用
    BT::NodeStatus onStart() override
    {
        new_command_available_ = false;
        return BT::NodeStatus::RUNNING;
    }

    // 节点运行中定期调用
    BT::NodeStatus onRunning() override
    {
        std::lock_guard<std::mutex> lock(mutex_);

        bool task_locked = false;
        getInput("task_locked", task_locked);

        if (new_command_available_)
        { 
            if(last_room_name_!= current_room_name_||last_task_command_!=current_task_command_)
            {
                if(task_locked)
                {
                    ROS_WARN_THROTTLE(5.0, "Task is locked, ignoring new command.");
                }
                else{
                    setOutput("nav_target_room", current_room_name_);
                    setOutput("voice_task_command", current_task_command_);
                    ROS_INFO("New command received: room=%s, task=%s", 
                            current_room_name_.c_str(), current_task_command_.c_str());           
                }
            }
            else{
                ROS_WARN_THROTTLE(5.0, "received same command.");
            }

            last_room_name_ = current_room_name_;
            last_task_command_ = current_task_command_;
            new_command_available_ = false;  
        }
        // 始终返回RUNNING，保持节点活动状态
        return BT::NodeStatus::RUNNING;
    }

    // 节点被中断时调用
    void onHalted() override
    {
        ROS_INFO("Command listener halted");
    }

private:
    void voiceCommandCallback(const agrobot_bt_manager::voice_command::ConstPtr& msg)
    {
 
        std::lock_guard<std::mutex> lock(mutex_);
        current_room_name_ = msg->room_name;
        current_task_command_ = msg->task_command;
        new_command_available_ = true;

    }

    void appCommandCallback(const agrobot_bt_manager::voice_command::ConstPtr& msg)
    {
        ROS_INFO(" new app Command listener");
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