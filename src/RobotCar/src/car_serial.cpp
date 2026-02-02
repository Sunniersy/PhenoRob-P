#include <ros/ros.h>
#include <ros/package.h>
#include <geometry_msgs/Twist.h>
#include <iostream>
#include <serial/serial.h>
#include <sstream>
#include <fstream>
#include <stdio.h>
#include <string.h>
#include "RobotCar/carinfo.h"
#include <arpa/inet.h>
#include "std_msgs/Int8.h"
#include <std_msgs/Bool.h>

using namespace std;
uint8_t CalcChecksum(uint8_t *pBuf, uint32_t nLength)
{
    uint8_t checksum = 0;
    for(uint8_t i = 0;i < (nLength-1);i++)
    {
        checksum ^= pBuf[i];
    }
    return checksum;
}

#pragma pack (1)
typedef struct _REPORT_DATA_  
{
	unsigned char Head_1;    
    unsigned char Head_2; 
    unsigned char cmd_1; 
    unsigned char flag_1;
    unsigned char flag_2;
	int Speed_X;	
    int Speed_Y;				
	int Speed_Z;			
    float power;		
	unsigned char  Sum; 				
}REPORT_DATA;

typedef struct _CMD_DATA_  
{
	unsigned char Head_1;    
    unsigned char Head_2; 
    unsigned char cmd_1; 
    unsigned char cmd_2;
    unsigned short mode1;
    unsigned short mode2;
	unsigned int  Speed_X;		
    unsigned int  Speed_Y;	
	unsigned int  Speed_Z;			
	unsigned char  Sum; 				
}CMD_DATA;
#pragma pack ()

enum ROBOT_COMMAND
{
    DIFF_SPEED = 0,
    TRANSPORT  = 1,
    GRIPPER    = 2,
    CHARGE     = 3,
};

typedef struct _ROBOT_DATA_ 
{
	ROBOT_COMMAND robot_command;
    unsigned short command_mode;
}ROBOT_DATA;
ROBOT_DATA robot_data;
//创建一个serial类
serial::Serial sp;

typedef union{   //定义一个共用体，用于double数据与16进制的转换
unsigned char cvalue[4];
float fvalue;
}float_union;
static uint8_t s_buffer[sizeof(CMD_DATA)];
static uint8_t r_buffer[36];
int16_t capturecmd = 0;

bool initSerialPort(const std::string& port_name = "/dev/STM32", 
                  uint32_t baudrate = 115200,
                  uint32_t timeout_ms = 100) 
{
    try {
        serial::Timeout to = serial::Timeout::simpleTimeout(timeout_ms);
        sp.setPort(port_name);
        sp.setBaudrate(baudrate);
        sp.setTimeout(to);
        sp.open();
        
        if(sp.isOpen()) {
            ROS_INFO_STREAM(port_name << " opened successfully.");
            return true;
        }
    } catch(const serial::IOException& e) {
        ROS_ERROR_STREAM("Failed to open port " << port_name << ": " << e.what());
    }
    return false;
}

void sendCommandToSTM32(uint16_t mode1, uint16_t mode2, int speed_x, int speed_y, int speed_z)
{
    CMD_DATA* cmd_data = new CMD_DATA;
    memset(s_buffer, 0, sizeof(s_buffer));

    cmd_data->Head_1 = 0xA0;
    cmd_data->Head_2 = 0x0A;
    cmd_data->cmd_1  = 0xAA;
    cmd_data->cmd_2  = 0x20;
    cmd_data->mode1  = mode1;
    cmd_data->mode2  = mode2;
    cmd_data->Speed_X = speed_x;
    cmd_data->Speed_Y = speed_y;
    cmd_data->Speed_Z = speed_z;
    cmd_data->Sum     = CalcChecksum((uint8_t*)cmd_data, sizeof(CMD_DATA));

    memcpy(s_buffer, cmd_data, sizeof(CMD_DATA));
    sp.write(s_buffer, sizeof(CMD_DATA));
    delete cmd_data;

    std::ostringstream oss;
    oss << "Send buffer (hex): ";
    for (size_t i = 0; i < sizeof(CMD_DATA); ++i) {
    oss << std::hex << std::uppercase << std::setw(2) << std::setfill('0')
        << static_cast<int>(static_cast<uint8_t>(s_buffer[i])) << " ";
    }
    ROS_INFO_STREAM(oss.str());
}


void cmd_callback(const geometry_msgs::Twist::ConstPtr& cmd_vel)
{
    robot_data.robot_command = DIFF_SPEED;
    robot_data.command_mode = 0;
    if (robot_data.robot_command != DIFF_SPEED) {
        ROS_WARN_THROTTLE(1.0, "Ignore cmd_vel: robot not in DIFF_SPEED mode.");
        return;
    }
    int speed_x = static_cast<int>(cmd_vel->linear.x * 1000);
    int speed_z = static_cast<int>(cmd_vel->angular.z * 1000);
    sendCommandToSTM32(robot_data.robot_command, robot_data.command_mode, speed_x, 0, speed_z);

    // CMD_DATA *cmd_data = new CMD_DATA;
 	// float_union linear_x ,angular_z;	
	// memset(s_buffer,0,sizeof(s_buffer));
	// linear_x.fvalue = cmd_vel->linear.x;
	// angular_z.fvalue = cmd_vel->angular.z;
    // cmd_data->Head_1 = 0xA0;
    // cmd_data->Head_2 = 0x0A;
    // cmd_data->cmd_1  = 0xAA;
    // cmd_data->cmd_2  = 0x20;
    // cmd_data->mode1   = robot_data.robot_command;
    // cmd_data->mode2   = robot_data.command_mode;
    // cmd_data->Speed_X = (int)(cmd_vel->linear.x*1000);
    // cmd_data->Speed_Y = 0x00;
    // cmd_data->Speed_Z = (int)(cmd_vel->angular.z*1000);
    // // ROS_INFO(" x= %d   z= %d" ,cmd_data->Speed_X,cmd_data->Speed_Z);
    // cmd_data->Sum = CalcChecksum((uint8_t*)cmd_data,sizeof(CMD_DATA));
    // memcpy(s_buffer,cmd_data,sizeof(CMD_DATA));
	// sp.write(s_buffer,sizeof(CMD_DATA));
    // delete cmd_data;
}

void processSerialData(ros::Publisher& pub, REPORT_DATA* report_data) {
    size_t n = sp.available();
    if(n == 0) return;

    uint8_t buffer[1024];
    n = sp.read(buffer, n);
    if(n >= sizeof(REPORT_DATA) && 
       buffer[0] == 0xA0 && 
       buffer[1] == 0x0A && 
       buffer[2] == 0x55) 
    {
        memcpy(report_data, buffer, sizeof(REPORT_DATA));
        RobotCar::carinfo car;
        car.speed_x = report_data->Speed_X;
        car.speed_z = report_data->Speed_Z;
        car.power = report_data->power;       
        pub.publish(car);
    }
}
void charge_start_callback(const std_msgs::Bool& msg)
{
    if(msg.data){
        robot_data.robot_command = CHARGE;//开始充电，设为充电状态
        robot_data.command_mode = 1;
        ROS_INFO("start_charge");
    }
    else
    {
        robot_data.robot_command = CHARGE;//结束充电后，恢复差速状态
        robot_data.command_mode = 0;
        ROS_INFO("end_charge");
    } 
    sendCommandToSTM32(robot_data.robot_command, robot_data.command_mode, 0, 0, 0);
}
int main(int argc, char** argv)
{
    REPORT_DATA *report_data = new REPORT_DATA();
	ros::init(argc, argv, "cmd_vel_listener");
	ros::NodeHandle n;

    if(!initSerialPort()) {
        ROS_ERROR("Serial port initialization failed!");
        delete report_data;
        return -1;
    }

	ros::Publisher pub  = n.advertise<RobotCar::carinfo>("CarInfo",10);
	ros::Subscriber sub = n.subscribe("/cmd_vel", 1000, cmd_callback); 
    ros::Subscriber chagre_start_sub = n.subscribe("/start_charging", 10, charge_start_callback); 
	ros::Rate loop_rate(20);
    robot_data.robot_command = DIFF_SPEED;
    robot_data.command_mode = 0;

	while(n.ok())
	{ 
        processSerialData(pub, report_data);
        ros::spinOnce();
		loop_rate.sleep();	
	}
	sp.close();
   // delete report_data;
	return 1;
}