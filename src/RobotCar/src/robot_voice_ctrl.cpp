#include <ros/ros.h>
#include <iostream>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <cstring>
#include <serial/serial.h>
#include <RobotCar/robotinfo.h>
#include "RobotCar/voice2robot.h"

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

uint8_t current_state = 0;
uint8_t last_state = 0;
int32_t current_room_num = -1;
bool is_navigating = false;                      // 是否正在导航

static uint8_t s_buffer[sizeof(CMD_DATA)];
// 语音命令定义
const uint8_t Open_door    = 0x5F;
const uint8_t Running      = 0x60;
const uint8_t Nav_failed   = 0x61;
const uint8_t Charge_start = 0x62;
const uint8_t Charge_stop  = 0x63;
const uint8_t Is_nav       = 0x64;
const uint8_t Voice_start  = 0x65;

ros::ServiceClient voice2robot_client;
RobotCar::voice2robot srv;
serial::Serial sp;

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

void processSerialData(REPORT_DATA* report_data) {
    size_t n = sp.available();
    if(n == 0) return;
    
    uint8_t buffer[1024];
    n = sp.read(buffer, n);
    std::ostringstream oss;
    oss << "Received " << n << " bytes: ";
    for (size_t i = 0; i < n; ++i) {
        oss << std::hex << std::uppercase << std::setw(2) 
        << std::setfill('0') << (int)buffer[i] << " ";
    }
    ROS_INFO_STREAM(oss.str());

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

        if(cmd == 0X00)
        {
            if(!is_navigating){
                
                if(result >= 0x01 && result <= 0x04)
                {
                    current_room_num = 1;
                }
                else if(result >= 0x04 && result <= 0x08)
                {
                    current_room_num = 0;
                }
                else if(result >= 0x09 && result <= 0x44)
                {
                    current_room_num = (result - 0x09)/4 + 4;
                }
                else
                {
                    current_room_num = -1;
                }
                

                if(current_room_num != -1){
                    
                    ROS_INFO("current_room_num = %d",current_room_num);
                    srv.request.room_point = current_room_num;
                    voice2robot_client.call(srv);
                }
            }
            else
            {
                ROS_INFO("robot is navigating");
                serial_write(Is_nav);
            }   
        }
    }
}



 
void robot_state_voice_command()
{
    if(last_state != current_state)
    {
        if(last_state == A_OPEN_DOOR || last_state == B_OPEN_DOOR && current_state == FINISH)
        {
            // serial_write(Open_door);
        }
        else if(current_state == RUNNING )
        {
            // serial_write(Running);
        }
        else if(current_state == FAILED )
        {
            serial_write(Nav_failed);
        }
        else if(current_state == CHARGE)
        {
            serial_write(Charge_start);
        }
        else if(current_state == START && last_state == STOP )
        {
            serial_write(Charge_stop);
        }
    }

    if(current_state == RUNNING || current_state == A_OPEN_DOOR || 
    current_state == B_OPEN_DOOR || current_state == CHARGE)
    {
        is_navigating = true;
    }
    else
    {
        is_navigating = false;
    }
    last_state = current_state;
}

void robotinfoCallback(const RobotCar::robotinfo& msg)
{
    current_state = msg.robotstate;
    robot_state_voice_command();
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

    ros::Subscriber sub = n.subscribe("/robot_info",10,robotinfoCallback);
    voice2robot_client = n.serviceClient<RobotCar::voice2robot>("voice2robot_server");
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
