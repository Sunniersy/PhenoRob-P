#include <ros/ros.h>
#include <iostream>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <cstring>
#include <serial/serial.h>
#include "agrobot_bt_manager/voice_command.h"

using namespace std;

typedef struct _REPORT_DATA_  
{
	unsigned char Head_1;    
    unsigned char Head_2; 
    unsigned char cmd; 
    unsigned char result;	
	unsigned char  Sum; 				
}REPORT_DATA;

typedef struct _CMD_DATA_  
{
	uint8_t Head_1;    
    uint8_t Head_2; 
    uint8_t cmd; 
    uint8_t mode;			
	uint8_t Sum; 				
}CMD_DATA;

uint8_t current_state = 0;
uint8_t last_state = 0;
bool is_navigating = false;                      // 是否正在导航
std::string last_room;
std::string last_task_command;

static uint8_t s_buffer[sizeof(CMD_DATA)];
// 语音命令定义
const uint8_t Open_door    = 0x5F;
const uint8_t Running      = 0x60;
const uint8_t Nav_failed   = 0x61;
const uint8_t Charge_start = 0x62;
const uint8_t Charge_stop  = 0x63;
const uint8_t Is_nav       = 0x64;
const uint8_t Voice_start  = 0x65;

serial::Serial sp;
ros::Publisher v_com_pub;
// ============串口初始化=================
bool initSerialPort(const std::string& port_name = "/dev/myspeech", 
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
// ============串口发送函数================
void serial_write(uint8_t mode)
{
    CMD_DATA *cmd_data = new CMD_DATA;
    memset(s_buffer,0,sizeof(s_buffer)); 

    cmd_data->Head_1 = 0xAA;
    cmd_data->Head_2 = 0x55;
    cmd_data->cmd    = 0xFF;
    cmd_data->mode   = mode;
    cmd_data->Sum    = 0XFB;
    memcpy(s_buffer,cmd_data,sizeof(CMD_DATA));
	sp.write(s_buffer,sizeof(CMD_DATA));
    delete cmd_data; 
}


// =============解析命令=============
std::string parseRoomNumber(uint8_t command_result) {
    if (command_result >= 0x01 && command_result <= 0x04) {
    return "charge_room_1";
    } else if (command_result >= 0x05 && command_result <= 0x08) {
    return "park_room";
    } else if (command_result >= 0x09 && command_result <= 0x44) {
    return "room_" + std::to_string((command_result - 0x09) / 4 + 1);
    }
    return "Invalid";
}
//=============解析串口数据==============
void processSerialData(REPORT_DATA* report_data) {
    size_t n = sp.available();
    if(n == 0) return;
    
    uint8_t buffer[1024];
    n = sp.read(buffer, n);
    // std::ostringstream oss;
    // oss << "Received " << n << " bytes: ";
    // for (size_t i = 0; i < n; ++i) {
    //     oss << std::hex << std::uppercase << std::setw(2) 
    //     << std::setfill('0') << (int)buffer[i] << " ";
    // }
    // ROS_INFO_STREAM(oss.str());

    if(n >= sizeof(REPORT_DATA) && 
       buffer[0] == 0xAA && 
       buffer[1] == 0x55 &&
       buffer[2] == 0x00 &&
       buffer[4] == 0xFB 
       ) 
    {
        memcpy(report_data, buffer, sizeof(REPORT_DATA));
        
        uint8_t cmd = report_data->cmd;
        uint8_t result = report_data->result;
        ROS_INFO("cmd = %x,result = %x",cmd,result);
        agrobot_bt_manager::voice_command voice_command;
        if(cmd == 0X00)
        {
            std::string room = parseRoomNumber(result);
            std::string task_command;
            if (room != "Invalid") {
                if(room == "charge_room_1")
                {
                    task_command = "Charge";
                }
                else if(room == "park_room")
                {
                    task_command = "Park";
                }
                else
                {
                    task_command = "Nav";
                }
                
                voice_command.room_name = room;
                voice_command.task_command = task_command;
                

                if(room != last_room||last_task_command != task_command)//这里的task_command是预留的命令接口,后续可以补充
                {
                    voice_command.new_voice_command = true;
                    last_room = room;
                    last_task_command = task_command;
                    ROS_INFO_STREAM("Published new room command: " << room);
                    ROS_INFO_STREAM("Published new room command: " << task_command);
                }
                else
                {
                    voice_command.new_voice_command = false;
                }

                v_com_pub.publish(voice_command); 
            }
        }
    }
}


int main(int argc, char** argv) { 
    REPORT_DATA *report_data = new REPORT_DATA();
	ros::init(argc, argv, "voice_ctrl");
	ros::NodeHandle n;

    if(!initSerialPort()) {
        ROS_ERROR("Serial port initialization failed!");
        delete report_data;
        return -1;
    }
    v_com_pub = n.advertise<agrobot_bt_manager::voice_command>("/voice_command", 10);
	ros::Rate loop_rate(20);
    serial_write(Voice_start);
	while(n.ok())
	{ 
        processSerialData(report_data);

        ros::spinOnce();
		loop_rate.sleep();	
	}
	sp.close();

	return 1;
}
