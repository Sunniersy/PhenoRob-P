#include "ros/ros.h"
#include "RobotCar/recorderpose.h"
#include <tf/transform_listener.h>
#include <fstream>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>

std::string csv_file_path; 

struct RoomPose {
    int id;
    double x, y, yaw;
    std::string name;
};

// 读取已有 CSV 并解析为 RoomPose 向量 
std::vector<RoomPose> readCSV(const std::string &filepath) {
    std::vector<RoomPose> poses;
    std::ifstream file(filepath);
    std::string line;

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        RoomPose pose;
        std::string value;

        std::getline(ss, value, ','); pose.id = std::stoi(value);
        std::getline(ss, value, ','); pose.x = std::stod(value);
        std::getline(ss, value, ','); pose.y = std::stod(value);
        std::getline(ss, value, ','); pose.yaw = std::stod(value);
        std::getline(ss, value, ','); pose.name = value;
        // 去除空白字符
        pose.name.erase(0, pose.name.find_first_not_of(" \t\r\n"));
        pose.name.erase(pose.name.find_last_not_of(" \t\r\n") + 1);
        poses.push_back(pose);
    }
    return poses;
}

// 写入 CSV
void writeCSV(const std::string &filepath, const std::vector<RoomPose> &poses) {
    std::ofstream file(filepath, std::ios::trunc);  // 覆盖写入
    for (const auto &pose : poses) {
        file << pose.id << ","
             << std::fixed << std::setprecision(3)
             << pose.x << ","
             << pose.y << ","
             << pose.yaw << ","
             << pose.name << "\n";
    }
    file.close();
}

bool recordPose(RobotCar::recorderpose::Request &req,
                RobotCar::recorderpose::Response &res)
{
    static tf::TransformListener listener;
    tf::StampedTransform transform;

    try {
        listener.waitForTransform("/map", "/base_link", ros::Time(0), ros::Duration(1.0));
        listener.lookupTransform("/map", "/base_link", ros::Time(0), transform);
    } catch (tf::TransformException &ex) {
        ROS_ERROR("TF Error: %s", ex.what());
        res.success = false;
        return true;
    }

    double x = transform.getOrigin().x();
    double y = transform.getOrigin().y();
    tf::Quaternion q = transform.getRotation();
    double roll, pitch, yaw;
    tf::Matrix3x3(q).getRPY(roll, pitch, yaw);

    std::string room_name = req.room_name;
    if (room_name.empty()) {
        ROS_WARN("Room name is empty. Skipping save.");
        res.success = false;
        return true;
    }

    std::vector<RoomPose> poses = readCSV(csv_file_path);
    bool found = false;

    // 如果已有此房间名，则更新
    for (auto &pose : poses) {
        if (pose.name == room_name) {
            pose.x = x;
            pose.y = y;
            pose.yaw = yaw;
            found = true;
            ROS_INFO("Room [%s] updated.", room_name.c_str());
            break;
        }
    }

    // 如果没有此房间，新增
    if (!found) {
        int next_id = poses.empty() ? 0 : poses.back().id + 1;
        poses.push_back(RoomPose{next_id, x, y, yaw, room_name});
        ROS_INFO("Room [%s] recorded as new.", room_name.c_str());
    }

    writeCSV(csv_file_path, poses);

    ROS_INFO("Saved pose: x=%.3f, y=%.3f, yaw=%.3f", x, y, yaw);
    res.success = true;
    return true;
}

int main(int argc, char **argv)
{
    ros::init(argc, argv, "pose_recorder_csv");
    ros::NodeHandle nh("~");

     // 加载 CSV 路径，可以通过参数传入
    std::string csv_file;
    if (!nh.getParam("csv_file_path", csv_file)) {
    ROS_ERROR("Failed to get parameter [csv_file_path]");
    return 1;
    }
    csv_file_path = csv_file; 

    ros::ServiceServer service = nh.advertiseService("record_pose", recordPose);
    ROS_INFO("Pose recorder service (CSV-based) is ready.");
    ros::spin();
    return 0;
}
