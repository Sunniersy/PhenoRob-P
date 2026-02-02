#include <ros/ros.h>
#include <std_msgs/String.h>
#include <agrobot_bt_manager/get_roompose.h>  // 替换为你的 package 名字
#include <fstream>
#include <sstream>
#include <string>
#include <map>

struct RoomPose {
    double x;
    double y;
    double yaw;
};

ros::Timer reload_timer;
std::string csv_file_path;
std::map<std::string, RoomPose> room_pose_map_;

// ===========获取房间坐标回调函数====================
bool getRoomPoseCallback(agrobot_bt_manager::get_roompose::Request& req,
                         agrobot_bt_manager::get_roompose::Response& res) {
    auto it = room_pose_map_.find(req.room_name);
    if (it != room_pose_map_.end()) {
        res.x = it->second.x;
        res.y = it->second.y;
        res.yaw = it->second.yaw;
        res.success = true;
        res.message = "Room found.";
    } else {
        res.success = false;
        res.message = "Room not found.";
    }
    return true;
}
// =================加载房间坐标====================
void reloadCSVCallback(const ros::TimerEvent&) {
    static std::map<std::string, RoomPose> new_room_pose_map;
    std::ifstream file(csv_file_path);
    if (!file.is_open()) {
        ROS_WARN_STREAM("Could not reload CSV: " << csv_file_path);
        return;
    }

    std::string line;
    new_room_pose_map.clear();
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        std::string token;
        int id;
        double x, y, yaw;
        std::string room_name;

        std::getline(ss, token, ','); id = std::stoi(token);
        std::getline(ss, token, ','); x = std::stod(token);
        std::getline(ss, token, ','); y = std::stod(token);
        std::getline(ss, token, ','); yaw = std::stod(token);
        std::getline(ss, token, ','); room_name = token;
        room_name.erase(0, room_name.find_first_not_of(" \t"));

        new_room_pose_map[room_name] = {x, y, yaw};
    }

    // 原子更新
    room_pose_map_ = new_room_pose_map;
    // ROS_INFO_STREAM("CSV reloaded. Rooms: " << room_pose_map_.size());
}

int main(int argc, char** argv) {
    ros::init(argc, argv, "room_pose_loader_node");
    ros::NodeHandle nh("~");

    // 加载 CSV 路径，可以通过参数传入
    std::string csv_file;
    if (!nh.getParam("csv_file_path", csv_file)) {
    ROS_ERROR("Failed to get parameter [csv_file_path]");
    return 1;
}

    csv_file_path = csv_file; 
    // 广播 Service
    ros::ServiceServer service = nh.advertiseService("/get_room_pose", getRoomPoseCallback);
    reload_timer = nh.createTimer(ros::Duration(5.0), reloadCSVCallback);
    ROS_INFO("RoomPoseLoader Service ready: get_room_pose");

    ros::spin();
    return 0;
}
