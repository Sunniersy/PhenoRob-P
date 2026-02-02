// nav_toroom/clear_global_costmap.h
#ifndef CLEAR_GLOBAL_COSTMAP_H
#define CLEAR_GLOBAL_COSTMAP_H

#include <behaviortree_cpp_v3/action_node.h>
#include <ros/ros.h>
#include <std_srvs/Empty.h>

using namespace BT;

class ClearGlobalCostmapNode : public SyncActionNode
{
public:
    ClearGlobalCostmapNode(const std::string& name, const NodeConfiguration& config)
        : SyncActionNode(name, config)
    {
        ros::NodeHandle nh;
        // 通常清除代价地图的服务名为 "/move_base/clear_costmaps"
        clear_costmap_client_ = nh.serviceClient<std_srvs::Empty>("/move_base/clear_costmaps");
        
        // 等待服务可用
        if (!clear_costmap_client_.waitForExistence(ros::Duration(5.0))) {
            ROS_WARN("Clear costmap service not available, will try again later");
        } else {
            ROS_INFO("Clear costmap service ready");
        }
    }

    static PortsList providedPorts()
    {
        return {
            BT::InputPort<std::string>("nav_target_room")
        }; // 这个节点不需要输入端口
    }

    NodeStatus tick() override
    {
        std_srvs::Empty srv;

        std::string nav_target_room;
        if (!getInput("nav_target_room", nav_target_room))
        {
            return BT::NodeStatus::SUCCESS;
        }
        if(last_nav_target_room_ == nav_target_room)
        {
            return BT::NodeStatus::SUCCESS;//房间没更新，直接不判断
        }

        last_nav_target_room_ = nav_target_room;
        
        if (!clear_costmap_client_.exists()) {
            // 如果服务不可用，尝试重新连接
            if (!clear_costmap_client_.waitForExistence(ros::Duration(0.5))) {
                ROS_WARN("Clear costmap service still not available");
               
            }
        }
        
        if (clear_costmap_client_.call(srv)) {
            ROS_INFO("Successfully cleared global costmap");
            
        } else {
            ROS_ERROR("Failed to call clear_costmap service");
        }
        return NodeStatus::SUCCESS;
    }

private:
    ros::ServiceClient clear_costmap_client_;
    std::string last_nav_target_room_;
};

#endif // CLEAR_GLOBAL_COSTMAP_H