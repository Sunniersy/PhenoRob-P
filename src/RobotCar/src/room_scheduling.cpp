#include "ros/ros.h" 
#include "std_msgs/String.h"
#include "move_base_msgs/MoveBaseAction.h"
#include "actionlib/client/simple_action_client.h"
#include "RobotCar/carinfo.h"
#include "RobotCar/robotinfo.h"
#include <sstream>
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include "RobotCar/voice2robot.h"
#include <tf/transform_datatypes.h>
#include "pattern_matcher/icpcharge.h"  // 服务头文件
#include <std_msgs/Bool.h>
#include <std_srvs/Empty.h>

using namespace std;

enum ROBOT_STATE
{
    STOP        = 0,
    RUNNING     = 1,
    A_OPEN_DOOR = 2,
    B_OPEN_DOOR = 3,
    FINISH      = 4,
    WAITTING    = 5,
    BACK_TO_0   = 6,
    CHARGE      = 7,
    FAILED      = 8,
    START       = 9,
    
};

#define CHARGE_ROOM 1
#define STOP_ROOM   0

int num = 0;

typedef struct ROBOT_INFO
{
    ROBOT_STATE robot_state;
    u_int8_t room_fresh_flag;
    int goal_point_num;
    int last_point_num;
    int robot_voltage; 
}robot_info;

robot_info robot;
move_base_msgs::MoveBaseGoal goal[40];//创建goal房间坐标点数组
typedef actionlib::SimpleActionClient<move_base_msgs::MoveBaseAction> MoveBaseClient;
ros::ServiceClient charge_srv;
ros::ServiceClient clear_costmap_client;
std_srvs::Empty empty_srv;
ros::Publisher charging_pub;

std::vector<std::string> split(const std::string &str, const std::string &pattern)
{
    char *strc = new char[strlen(str.c_str()) + 1];
    strcpy(strc, str.c_str()); // string转换成C-string
    std::vector<std::string> res;
    char *temp = strtok(strc, pattern.c_str());
    while (temp != NULL)
    {
        res.push_back(std::string(temp));
        temp = strtok(NULL, pattern.c_str());
    }
    delete[] strc;
    return res;
}

void voltage_callback(const RobotCar::carinfo &car)
{
    robot.robot_voltage = car.power;
}

bool voice2robot_callback(RobotCar::voice2robot::Request& req,RobotCar::voice2robot::Response& res)
{
    if(robot.room_fresh_flag == 0)//只允许在启动和等待状态下更新房间点
    {
        if(req.room_point==2||req.room_point==3||req.room_point>num)
        {
            ROS_ERROR("room_point is out of range!");
            res.roompoint_check = false;
            return true;
        }
        else
        {
            ROS_INFO("receive a new roompoint");
            robot.goal_point_num = req.room_point;
            robot.room_fresh_flag = 1;//房间刷新
            res.roompoint_check = true;
            return true;
        }
    }
    return 0;
}
void handleStartState(MoveBaseClient& client)
{
    // ROS_INFO("goal point:%d", robot.goal_point_num); 
    if(robot.goal_point_num > num)//目标点超出房间号
    {
        ROS_INFO("DIDN`T find this room point: %d", robot.goal_point_num);
    }
    else if(robot.goal_point_num == robot.last_point_num)
    {
        // ROS_INFO("goal never fresh");
    }
    else
    {
        if(robot.goal_point_num <= 16 && robot.goal_point_num >= 8)//目标点在8-16中
        {
            if(robot.last_point_num <= 16 && robot.last_point_num >= 8)//机器人当前位置在8-16中，直接前往目标点
            {
                ROS_INFO("goal has sended");
                client.sendGoal(goal[robot.goal_point_num]);//发送目标值
                robot.robot_state = RUNNING;
            }
            else//机器人当前位置不在4-10中，先去开门A点
            {
                ROS_INFO("go to A to open door"); 
                client.sendGoal(goal[2]);//发送开门点A目标值
                robot.robot_state = A_OPEN_DOOR;
            }
        }
        else//目标点不在4-10中
        {
            if(robot.last_point_num <= 16 && robot.last_point_num >= 8)//机器人当前位置在4-10中，先去B开门
            {
                ROS_INFO("go to B to open door");
                client.sendGoal(goal[3]);//发送开门点B目标值
                robot.robot_state = B_OPEN_DOOR;
            }
            else//机器人当前位置不在4-10中，直接前往目标点
            {
                ROS_INFO("goal has sended");
                client.sendGoal(goal[robot.goal_point_num]);//发送目标值
                robot.robot_state = RUNNING;
            }
        }
    }
}
void handleRunningState(MoveBaseClient& client)
{
    client.waitForResult();
    if(client.getState() == actionlib::SimpleClientGoalState::SUCCEEDED)
    {
        robot.robot_state = FINISH;
        ROS_INFO("goal reached");
    }
    else
    {
        ROS_INFO("Goal failed");
        robot.robot_state = FAILED;
    }

}

void handle_A_DoorOpenState(MoveBaseClient& client)
{
    client.waitForResult();
    if(client.getState() == actionlib::SimpleClientGoalState::SUCCEEDED)
    {
        //open_door();//开门
        ROS_INFO("open door");
        ros::Duration(5.0).sleep();//等待10s//开门后前往
        client.sendGoal(goal[robot.goal_point_num]);
        ROS_INFO("go to goal");
        robot.robot_state = RUNNING;
        robot.last_point_num = 2;//刷新机器人上一次目标点为关门点
    }
    else
    {
        ROS_INFO("Goal failed");
        robot.robot_state = FAILED;
    }
}

void handle_B_OpenDoorState(MoveBaseClient& client)
{
    client.waitForResult();
    if(client.getState() == actionlib::SimpleClientGoalState::SUCCEEDED)
    {
        //open_door();//开门
        ROS_INFO("open door");
        ros::Duration(6.0).sleep();//等待10s
        client.sendGoal(goal[robot.goal_point_num]);//开门后前往
        ROS_INFO("go to goal");
        robot.robot_state = RUNNING;
        robot.last_point_num = 3;//刷新机器人上一次目标点为关门点
    }
    else
    {
        ROS_INFO("Goal failed");
        robot.robot_state = FAILED;
    }
}
void handleFinishState()
{
    if (clear_costmap_client.call(empty_srv)) {
        ROS_INFO("Costmaps cleared successfully before sending goal.");
    } else {
        ROS_WARN("Failed to clear costmaps before sending goal.");
    }

    robot.last_point_num = robot.goal_point_num;//刷新机器人上一次目标点
    robot.room_fresh_flag = 0;//房间刷新
    if(robot.goal_point_num == CHARGE_ROOM)//如果目标点是充电位，则启动自动充电
    {
        robot.robot_state = CHARGE;
    }
    else
    {
        robot.robot_state = WAITTING;//机器人进入等待状态，等待下一次任务下发
    }
    
}
bool ismove= false;
ros::Time start_wait_time;
void handleWaitingState()
{
    if(!ismove){
        start_wait_time = ros::Time::now();
        ismove = true;
    }
    if(robot.room_fresh_flag)//目标点更新
    {
        robot.robot_state = START;
        ismove = false;
    }
    else if((ros::Time::now() - start_wait_time).toSec() > 120)//300s内没有下发任务
    {
        ROS_INFO("waitting for 300s,NO GOAL FRESH");
        robot.robot_state = BACK_TO_0; 
        ismove = false;
    }
}
void handleBackToZEROState()
{
    ROS_INFO("back to charge_point");
    robot.goal_point_num = STOP_ROOM;//目标点设为停车点
    robot.room_fresh_flag = 1;
    ros::Duration(1.0).sleep();
    robot.robot_state = START;//置为start，机器人开始规划返回路线
}
void handleChargeState() {
    std_msgs::Bool msg;
    msg.data = true;  //开启ICP匹配
    charging_pub.publish(msg);

    pattern_matcher::icpcharge srv;
    srv.request.charge_enable = true;  // 启用充电
    srv.request.charge_stop = false;   // 确保停止标志为false
    
    if (charge_srv.call(srv)) {
        if(srv.response.current_charging == 1) {
            robot.robot_state = STOP;
            robot.room_fresh_flag = 0;//允许更新房间
        }
        else
        {
            // robot.robot_state = WAITTING;
        }
    } else {
        ROS_ERROR("Failed to call charge control service when starting charge");
        robot.robot_state = WAITTING;
    }
}
void handleStopState() {
    ROS_INFO("room_fresh_flag: %d", robot.room_fresh_flag);
    if(robot.room_fresh_flag) {
        ROS_INFO("stop charge");

        pattern_matcher::icpcharge srv;
        srv.request.charge_enable = false;  // 禁用充电
        srv.request.charge_stop = true;     // 发送停止命令
        
        if (charge_srv.call(srv)) {
            if(srv.response.current_charging == 0) {
                robot.robot_state = START;
                std_msgs::Bool msg;
                msg.data = false;  //关闭ICP匹配
                charging_pub.publish(msg);
            }
        } else {
            ROS_ERROR("Failed to call charge control service when stopping charge");
        }
    }
}
void handleFailureState()
{
    if (clear_costmap_client.call(empty_srv)) {
        ROS_INFO("Costmaps cleared successfully before sending goal.");
    } else {
        ROS_WARN("Failed to clear costmaps before sending goal.");
    }

    ROS_INFO("back to charge_point");
    robot.goal_point_num = STOP_ROOM;//目标点设为停车点
    robot.room_fresh_flag = 1;
    ros::Duration(1.0).sleep();
    robot.robot_state = START;//置为start，机器人开始规划返回路线          
}
void RobotStateManager(MoveBaseClient& client)
{
     switch (robot.robot_state)
        {
            case START:
                handleStartState(client);
                break;
            case RUNNING:
                handleRunningState(client);
                break;
            case A_OPEN_DOOR:
                handle_A_DoorOpenState(client);
                break;
            case B_OPEN_DOOR:
                handle_B_OpenDoorState(client);
                break;
            case FINISH:
                handleFinishState();
                break;
            case WAITTING:
                handleWaitingState();
                break;
            case BACK_TO_0:
                handleBackToZEROState();
                break;
            case FAILED:
                handleFailureState();//机器人导航失败，此处应该需要更加完整的错误处理方法
                break;
            case CHARGE:
                handleChargeState();
                break;
            case STOP:
                handleStopState();
                break;
            default:
                ROS_ERROR("Unknown state");
                break;
        }
}
 
int main(int argc, char **argv)
{
    std::setlocale(LC_ALL, "C");
    ros::init(argc,argv,"robot_room_scheddule");
    ros::NodeHandle nh;
    ros::Subscriber power_sub = nh.subscribe("/CarInfo",1000,voltage_callback);
    charging_pub = nh.advertise<std_msgs::Bool>("/charging_task_active", 1);
    ros::ServiceServer  voice_server = nh.advertiseService("voice2robot_server",voice2robot_callback);
    ros::Publisher robotinfo_pub = nh.advertise<RobotCar::robotinfo>("robot_info",10);
    charge_srv = nh.serviceClient<pattern_matcher::icpcharge>("/icp_charge");
    clear_costmap_client = ros::NodeHandle().serviceClient<std_srvs::Empty>("/move_base/clear_costmaps");
    std::ifstream csv_data("/home/agrobot2/Robot_oradar_ws/points.csv", std::ios::in);
    if (!csv_data)
    {
        std::cout << "open .csv failed" << std::endl;
        ROS_ERROR(" .csv  doesn't exisit ");
        std::exit(1);
    }
    std::string line;
    std::vector<std::string> strbuf;
    while (std::getline(csv_data, line))//读取房间坐标
    {
        std::cout << line << std::endl;
        strbuf = split(line, ",");
        goal[num].target_pose.header.frame_id = "map";
        goal[num].target_pose.header.stamp = ros::Time::now();
        goal[num].target_pose.pose.position.x = atof(strbuf[1].c_str());
        goal[num].target_pose.pose.position.y = atof(strbuf[2].c_str());
        double yaw = atof(strbuf[3].c_str()); // 第4列是yaw角，单位是弧度
        ROS_INFO("Parsed x=%.6f, y=%.6f, yaw=%.6f", 
        goal[num].target_pose.pose.position.x,
        goal[num].target_pose.pose.position.y,
        yaw);
        geometry_msgs::Quaternion q = tf::createQuaternionMsgFromYaw(yaw);
        goal[num].target_pose.pose.orientation = q;
        num++;
    }
    MoveBaseClient client("move_base",true);
    client.waitForServer();
    ROS_INFO("server started!");

    robot.robot_state     = START;
    robot.room_fresh_flag = 0;
    robot.goal_point_num  = 0;
    robot.last_point_num  = 0;
    robot.robot_voltage   = 0;
    ros::Rate rate(5);
    while(ros::ok())
    {
        RobotStateManager(client);
        RobotCar::robotinfo info;
        info.robotstate = robot.robot_state;
        info.robotvoltage = robot.robot_voltage;
        info.lastroompoint = robot.last_point_num;
        robotinfo_pub.publish(info);
        ros::spinOnce();
        rate.sleep();
    }
    return 0;
}