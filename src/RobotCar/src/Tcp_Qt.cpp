#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>
#include <ros/ros.h>
#include <std_msgs/Float64MultiArray.h>
#include <mqtt/async_client.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <iomanip>
#include <nav_msgs/OccupancyGrid.h>
#include <geometry_msgs/TransformStamped.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include "RobotCar/carinfo.h"
#include <mutex>
#include <std_msgs/Bool.h>
#include "agrobot_bt_manager/voice_command.h"
#include "RobotCar/recorderpose.h"
#include "agrobot_bt_manager/arrived_point.h"

// ====== 函数前向声明 ======
void mqtt_message_callback(mqtt::const_message_ptr msg);

// ====== 常量定义 ======
#define MQTT_SERVER_ADDRESS "tcp://8.130.101.241:61613"
#define MQTT_CLIENT_ID "robot_pheno_1"
#define MQTT_TOPIC "robot_pheno_1"
#define MQTT_PHOTO_TOPIC "robot_photo1" 
#define MQTT_DOOR_TOPIC "esp32sub" 
// ====== 全局变量 ======
int server_fd = -1, client_fd = -1; // 客户端连接句柄，默认-1表示没有连接
int map_width = 0, map_height = 0;
double map_resolution = 0.0;
std::vector<int8_t> map_data;
double map_origin_x = 0.0, map_origin_y = 0.0;
double x_value = 0.0, y_value = 0.0, theta_value = 0.0;
int32_t power = 0.0;
int32_t room_count;
std::mutex data_mutex;
mqtt::async_client* mqtt_client = nullptr;
ros::Publisher task_pub;
ros::ServiceClient recorder_srv;
bool robot_arrived=false;
std::string arrived_room;
int count=0;
bool door_cmd = false;
std::string csv_file_path;

struct _AGROBOT_COMMAND_
{
    std::string task_head;
    std::string task_type;
    std::string target_room;
    std::string last_task_type;
    std::string last_target_room;
}AGROBOT_COMMAND;
_AGROBOT_COMMAND_ Agrobot_comm;

// ==========房间数量加载======
int countRoomEntries(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        ROS_ERROR("Failed to open file: %s", filename.c_str());
        return -1;
    }

    int room_count = 0;
    std::string line;

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string id_str, x_str, y_str, yaw_str, room_name;

        std::getline(ss, id_str, ',');
        std::getline(ss, x_str, ',');
        std::getline(ss, y_str, ',');
        std::getline(ss, yaw_str, ',');
        std::getline(ss, room_name, ',');

        // 去除前后空格
        room_name.erase(0, room_name.find_first_not_of(" \t"));
        room_name.erase(room_name.find_last_not_of(" \t\r\n") + 1);

        if (room_name.find("room_") == 0) {
            room_count++;
        }
    }

    file.close();
    return room_count;
}

// ==========地图数据=========
void mapCallback(const nav_msgs::OccupancyGrid::ConstPtr& msg)
{
    ROS_INFO("map");
    std::lock_guard<std::mutex> lock(data_mutex);
    map_width = msg->info.width;
    map_height = msg->info.height;
    map_resolution = msg->info.resolution;
    map_data = msg->data;
    map_origin_x = msg->info.origin.position.x;
    map_origin_y = msg->info.origin.position.y;
}

void messageCallback(const RobotCar::carinfo& car) //获取上篇文章串口功能包发来的数据
{
    power = car.power;
}

void doorCallback(const std_msgs::Bool& data)
{
    door_cmd = data.data;
    if(door_cmd)
    {
        std::string resp;
        resp = "LED_ON";
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_DOOR_TOPIC, resp);
        mqtt_client->publish(pubmsg);
        ROS_INFO("opendoor");
    }
}
void arrivedCallback(const agrobot_bt_manager::arrived_point::ConstPtr &msg)
{
    robot_arrived = msg->arrived;
    arrived_room = msg->room_name;
    // ROS_INFO_STREAM("arrived room name:" << arrived_room);
}
// =========机器人任务命令解析=============
void agrobotcommandHandler()
{
    agrobot_bt_manager::voice_command task_com;
    if(Agrobot_comm.task_head == "Task")
    {   //解析命令
        if(Agrobot_comm.task_type == "Charge")
        {
            task_com.task_command = "Charge";
            if(Agrobot_comm.target_room == "charge_room_1")//充电点选择
            {
                task_com.room_name = "charge_room_1";
            }
            
        }
        else if(Agrobot_comm.task_type == "Park")
        {
            task_com.task_command = "Park";
            if(Agrobot_comm.target_room == "park_room")//停车点选择
            {
                task_com.room_name = "park_room";
            }
            
        }
        else if(Agrobot_comm.task_type == "Nav")
        {
            task_com.task_command = "Nav";
            task_com.room_name = Agrobot_comm.target_room;
        }
        else if(Agrobot_comm.task_type == "stop_charge")
        {
            task_com.task_command = "Stopcharge";
            task_com.room_name = "";
        }
        else
        {
            ROS_INFO("unkown task command");
        }
        // 判定是否是新命令
        if(Agrobot_comm.last_target_room != Agrobot_comm.target_room || Agrobot_comm.last_task_type != Agrobot_comm.task_type)
        {
            task_com.new_voice_command = true;
            Agrobot_comm.last_target_room = Agrobot_comm.target_room;
            Agrobot_comm.last_task_type = Agrobot_comm.task_type;
            ROS_INFO_STREAM("Published new room command: " << Agrobot_comm.target_room);
            ROS_INFO_STREAM("Published new room command: " << Agrobot_comm.task_type);
        }
        else{
            task_com.new_voice_command = false;
        }
        // 发布命令
        task_pub.publish(task_com);
    }
}
// ====== 处理接收到的 MQTT 命令 ======
void mqtt_command_handler(const std::string& command, char* response) {
    if (command == "connect_robot") 
    {
        strcpy(response, "robot_connected");
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, response);
        mqtt_client->publish(pubmsg);
    }
    else if (command == "robot_power") //机器人电量
    {
        std::lock_guard<std::mutex> lock(data_mutex);
        std::string resp;
        resp = "robot_power,"+ std::to_string(power);
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, resp);
        mqtt_client->publish(pubmsg);
    }
    else if (command == "rebuild_map") //加载地图
    {
        std::string resp;
        std::lock_guard<std::mutex> lock(data_mutex);
        ROS_INFO("rebuild_map");

        if (!map_data.empty()) {
            std::ostringstream oss;
            for (auto& val : map_data) {
                oss << (val == -1 ? 2 : val);
            }
            resp = "map," + std::to_string(map_width) + "," +
                    std::to_string(map_height) + "," + oss.str() + "!";
        } else {
            resp = "no_map_data";
        }
        // MQTT 发送：直接传 std::string
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, resp);
        mqtt_client->publish(pubmsg);
        return;
    }else if(command == "world_pose")//查询世界坐标系
    {
        ROS_INFO("world_pose");
        std::lock_guard<std::mutex> lock(data_mutex);
        std::string resp;
        std::string x = std::to_string(map_origin_x);
        std::string y = std::to_string(map_origin_y);
        resp = "world_pose," + x + "," + y; 
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, resp);
        mqtt_client->publish(pubmsg);
    }
    else if (command == "pose_send") //查询机器人坐标
    {
        // ROS_INFO("pose_send");
        std::lock_guard<std::mutex> lock(data_mutex);
        std::string resp;
        std::string x = std::to_string(x_value);
        std::string y = std::to_string(y_value);
        std::string theta = std::to_string(theta_value);
        // ROS_INFO("robot pose: %s", oss.c_str());
        resp = "recv_pose," + x + "," + y + "," + theta;
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, resp);
        mqtt_client->publish(pubmsg);
    }
    else if(command.find("Task",0) == 0) //任务下发
    {
        std::string str = command;
        std::vector<std::string> strs;
        std::stringstream ss(str);
        std::string temp;
        while (std::getline(ss, temp, ',')) {
            strs.push_back(temp);
        }
        Agrobot_comm.task_head = strs[0];
        Agrobot_comm.task_type = strs[1];
        Agrobot_comm.target_room = strs[2];
        agrobotcommandHandler();//任务解析

        strcpy(response, "received_taskcommand");
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, response);
        mqtt_client->publish(pubmsg);
    }
    else if(command == "room")//加载当前房间个数
    {
        std::lock_guard<std::mutex> lock(data_mutex);
        std::string resp;
        resp = "room," + std::to_string(room_count);
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, resp);
        mqtt_client->publish(pubmsg);
    }
    else if(command.find("recorder_pose",0) == 0 )//房间坐标标定
    {
        std::string str = command;
        std::vector<std::string> strs;
        std::stringstream ss(str);
        std::string temp;
        while (std::getline(ss, temp, ',')) {
            strs.push_back(temp);
        }

        std::string recorder_room_name = strs[1];
        // ROS_INFO_STREAM("recorder room name:" << recorder_room_name);

        RobotCar::recorderpose srv;
        srv.request.room_name = recorder_room_name;
        if(recorder_srv.call(srv))
        {
            if(srv.response.success == true)
            {
                ROS_INFO_STREAM("recorder room pose success:" << recorder_room_name);              
            }
        }
        else
        {
            ROS_INFO_STREAM("Failed to call recorder srv");
        }
        
    }
    else {
        // strcpy(response, "unknown_command");
    }
}

// ====== MQTT 消息回调函数 ======
void mqtt_message_callback(mqtt::const_message_ptr msg) {
    std::string command = msg->to_string();
    char response[1024000];

    mqtt_command_handler(command, response);
}
void robot_arrived_pub()
{
    if(robot_arrived){
        robot_arrived = false;
        
        std::string res;
        res = "arrived,"+arrived_room;
        mqtt::message_ptr msg = mqtt::make_message(MQTT_TOPIC, res);
        mqtt_client->publish(msg);
        ROS_INFO_STREAM("arrived room name:" << arrived_room);
    }
}
// ====== 启动 MQTT 客户端 ======
void start_mqtt_client() { 
    mqtt::connect_options conn_opts;
    conn_opts.set_keep_alive_interval(20);

    mqtt_client = new mqtt::async_client(MQTT_SERVER_ADDRESS, MQTT_CLIENT_ID);

    mqtt_client->set_connection_lost_handler([](const std::string& cause) {
        printf("Connection lost: %s\n", cause.c_str());
    });

    mqtt_client->set_message_callback(mqtt_message_callback);

    mqtt_client->connect(conn_opts)->wait();
    printf("Connected to MQTT broker at %s\n", MQTT_SERVER_ADDRESS);

    mqtt_client->subscribe(MQTT_TOPIC, 1);
    mqtt_client->subscribe(MQTT_PHOTO_TOPIC, 1);
    mqtt_client->subscribe(MQTT_DOOR_TOPIC,1);
}

// ====== MQTT 线程函数 ======
void* mqtt_client_thread(void* arg) {
    start_mqtt_client();
    return NULL;
}
//判断客户端连接
void check_service_conect()
{
    count++;
    if(count >= 15)
    {
        count = 0;
        
        std::string resp;
        resp = "client_start,1";
        mqtt::message_ptr pubmsg = mqtt::make_message(MQTT_TOPIC, resp);
        mqtt_client->publish(pubmsg);
        // ROS_INFO_STREAM("client_start");
    }
}

// ====== 主函数 ======
int main(int argc, char** argv) {
    ros::init(argc, argv, "gps_listener");
    ros::NodeHandle nh("~");

    ros::Subscriber map_sub = nh.subscribe("/map", 10, mapCallback);
    ros::Subscriber door_sub = nh.subscribe("/door_command", 10, doorCallback);
    ros::Subscriber power_sub = nh.subscribe("/CarInfo", 1, messageCallback);
    task_pub = nh.advertise<agrobot_bt_manager::voice_command>("/app_command",100);
    recorder_srv = nh.serviceClient<RobotCar::recorderpose>("/roompose_recorder/record_pose",10);
    ros::Subscriber arived_sub = nh.subscribe("/arrived_point", 10, arrivedCallback);

    pthread_t mqtt_thread;
    if (pthread_create(&mqtt_thread, NULL, mqtt_client_thread, NULL) != 0) {
        perror("Error creating MQTT client thread");
        return -1;
    }
    tf2_ros::Buffer buffer;
    tf2_ros::TransformListener listener(buffer);

    std::string csv_file;
    if (!nh.getParam("csv_file_path", csv_file)) {
    ROS_ERROR(" QT Failed to get parameter [csv_file_path]");
    return 1;
    }
    room_count = countRoomEntries(csv_file);
    if (room_count >= 0) {
        ROS_INFO("Number of room_ entries: %d", room_count);
    }

    ros::Rate loop_rate(5);
    while (ros::ok()) {
        try
        {
            geometry_msgs::TransformStamped transformStamped = buffer.lookupTransform("map", "base_footprint", ros::Time(0), ros::Duration(5.0));
            std::lock_guard<std::mutex> lock(data_mutex);
            x_value = transformStamped.transform.translation.x;
            y_value = transformStamped.transform.translation.y;
            theta_value = transformStamped.transform.rotation.z;
            // ROS_INFO("map to base_footprint: x = %f, y = %f, theta = %f", x_value, y_value, theta_value);
        }
        catch (tf2::TransformException &ex)
        {
            ROS_WARN("TF Exception: %s", ex.what());
        }
        check_service_conect();
        robot_arrived_pub();
        ros::spinOnce();
        loop_rate.sleep();
    }

    return 0;
}
