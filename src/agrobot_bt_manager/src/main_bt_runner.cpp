// main_bt_runner.cpp
#include <behaviortree_cpp_v3/bt_factory.h>
#include <behaviortree_cpp_v3/xml_parsing.h>
#include "behaviortree_cpp_v3/loggers/bt_cout_logger.h"
#include "ros/ros.h"

#include "charge_control/dockto_charge_station.h"
#include "charge_control/locate_charge_station.h"
#include "voice_control/wait_fornew_commanddondition.h"
#include "nav_toroom/check_ifneed_opendoor.h"
#include "opendoor/open_door_action.h"
#include "nav_toroom/at_targetpose_condition.h"
#include "task_handler/is_command_condition.h"
#include "task_handler/wait_attarget_pose.h"
#include "task_handler/setrobotstatus.h"
#include "nav_toroom/navgation.h"
#include "nav_toroom/clear_costmap.h"
#include "voice_control/Taskupdata.h"
#include "nav_toroom/goalupdata.h"
#include "task_handler/alwaysrunning.h"
#include "task_handler/cleartaskcommand.h"
#include "charge_control/ischargingCondition.h"
#include "charge_control/stopchargeaction.h"

int main(int argc, char** argv)
{
    ros::init(argc, argv, "charging_bt_runner");
    ros::NodeHandle nh;

    // 添加BT节点
    BT::BehaviorTreeFactory factory;
    factory.registerNodeType<LocateChargingStation>("LocateChargingStation");
    factory.registerNodeType<DockToChargingStation>("DockToChargingStation");
    factory.registerNodeType<WaitForNewCommandCondition>("WaitForNewCommandCondition");
    factory.registerNodeType<CheckIfNeedOpenDoor>("CheckIfNeedOpenDoor");
    factory.registerNodeType<OpenDoorAction>("OpenDoorAction");
    factory.registerNodeType<AtTargetRoomCondition>("AtTargetRoomCondition");
    factory.registerNodeType<IsCommand>("IsCommand");
    factory.registerNodeType<WaitAtTargetPose>("WaitAtTargetPose");
    factory.registerNodeType<SetRobotStatusNode>("SetRobotStatusNode");
    factory.registerNodeType<MoveBaseToRoom>("MoveBaseToRoom");
    factory.registerNodeType<ClearGlobalCostmapNode>("ClearGlobalCostmapNode");
    factory.registerNodeType<AsyncCommandListener>("NewTaskListener");
    factory.registerNodeType<GoalUpdateCondition>("GoalUpdate");
    factory.registerNodeType<AlwaysRunning>("AlwaysRunning");
    factory.registerNodeType<ClearTaskCommandNode>("ClearTaskCommand");
    factory.registerNodeType<IsChargingCondition>("IsChargingCondition");
    factory.registerNodeType<StopChargingAction>("StopChargingAction");

    // 从 XML 文件加载树
    auto tree = factory.createTreeFromFile("/home/agrobot2/Bt_robot_ws/src/agrobot_bt_manager/bt_trees/nav_tree.xml");

    tree.rootBlackboard()->set("task_locked", false);
    tree.rootBlackboard()->set("IsCharging",false);

    BT::StdCoutLogger logger(tree);

    ros::Rate rate(1);
    while (ros::ok())
    {
        tree.tickRoot();
        ros::spinOnce();
        rate.sleep();
    }
    return 0;
}
