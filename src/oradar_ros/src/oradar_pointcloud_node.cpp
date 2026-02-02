#ifdef ROS_FOUND
#include <ros/ros.h>
#include <sensor_msgs/PointCloud.h>
#elif ROS2_FOUND
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud.hpp>
#endif
#include <cmath>
#include <unistd.h>
#include <arpa/inet.h>
#include "ord/ord_driver.h"

#define Degree2Rad(X) ((X)*M_PI / 180.)

// using namespace ord_sdk;
std::unique_ptr<ord_sdk::OrdDriver> device = NULL;

#ifdef ROS_FOUND
void publish_msg(ros::Publisher *pub, ord_sdk::ScanFrameData &scan_frame, ros::Time start,
                 double scan_time, std::string frame_id, bool inverted,
                 double angle_min, double angle_max, double min_range, double max_range)
{
  sensor_msgs::PointCloud pcMsg;
  int node_count = scan_frame.layers[0].ranges.size();
  int counts = node_count * ((angle_max - angle_min) / 270.0f);
  int angle_start = 135 + angle_min;
  int node_start = node_count * (angle_start / 270.0f);
  float range = 0.0;
  float intensity = 0.0;
  double angle_increment = (angle_max - angle_min) / (double)counts;
  double angle = 0.0, rad = 0.0;

  // ROS_INFO("get lidar frame count = %d, %d, %d, %d ", node_count, counts, angle_start, node_start);

  pcMsg.header.stamp = start;
  pcMsg.header.frame_id = frame_id;
  pcMsg.points.resize(counts);

  // add an intensity channel to the cloud
  pcMsg.channels.resize(1);
  pcMsg.channels[0].name = "intensities";
  pcMsg.channels[0].values.resize(counts);

  for (int i = 0; i < counts; i++)
  {
    range = scan_frame.layers[0].ranges[node_start] * 0.002;
    intensity = scan_frame.layers[0].intensities[node_start];
    angle = angle_increment * i + angle_min;
    rad = Degree2Rad(angle);

    if ((range >= min_range) && (range <= max_range))
    {
      if (!inverted)
      {
        pcMsg.points[i].x = range * cos(rad);
        pcMsg.points[i].y = range * sin(rad);
        pcMsg.points[i].z = 0.0;
        pcMsg.channels[0].values[i] = intensity;
        // node_start = node_start + 1;
      }
      else
      {
        pcMsg.points[counts - 1 - i].x = range * cos(rad);
        pcMsg.points[counts - 1 - i].y = range * sin(rad);
        pcMsg.points[counts - 1 - i].z = 0.0;
        pcMsg.channels[0].values[counts - 1 - i] = intensity;
        // node_start = node_start + 1;
      }
    }

    node_start = node_start + 1;
  }

  pub->publish(pcMsg);
}
#elif ROS2_FOUND
void publish_msg(rclcpp::Publisher<sensor_msgs::msg::PointCloud>::SharedPtr &pub, ord_sdk::ScanFrameData &scan_frame, rclcpp::Time start,
                 double scan_time, std::string frame_id, bool inverted,
                 double angle_min, double angle_max, double min_range, double max_range)
{
  sensor_msgs::msg::PointCloud pcMsg;
  int node_count = scan_frame.layers[0].ranges.size();
  int counts = node_count * ((angle_max - angle_min) / 270.0f);
  int angle_start = 135 + angle_min;
  int node_start = node_count * (angle_start / 270.0f);
  float range = 0.0;
  float intensity = 0.0;
  double angle_increment = (angle_max - angle_min) / (double)counts;
  double angle = 0.0, rad = 0.0;

  // ROS_INFO("get lidar frame count = %d, %d, %d, %d ", node_count, counts, angle_start, node_start);

  pcMsg.header.stamp = start;
  pcMsg.header.frame_id = frame_id;
  pcMsg.points.resize(counts);

  // add an intensity channel to the cloud
  pcMsg.channels.resize(1);
  pcMsg.channels[0].name = "intensities";
  pcMsg.channels[0].values.resize(counts);

  for (int i = 0; i < counts; i++)
  {
    range = scan_frame.layers[0].ranges[node_start] * 0.002;
    intensity = scan_frame.layers[0].intensities[node_start];
    angle = angle_increment * i + angle_min;
    rad = Degree2Rad(angle);

    if ((range >= min_range) && (range <= max_range))
    {
      if (!inverted)
      {
        pcMsg.points[i].x = range * cos(rad);
        pcMsg.points[i].y = range * sin(rad);
        pcMsg.points[i].z = 0.0;
        pcMsg.channels[0].values[i] = intensity;
        // node_start = node_start + 1;
      }
      else
      {
        pcMsg.points[counts - 1 - i].x = range * cos(rad);
        pcMsg.points[counts - 1 - i].y = range * sin(rad);
        pcMsg.points[counts - 1 - i].z = 0.0;
        pcMsg.channels[0].values[counts - 1 - i] = intensity;
        // node_start = node_start + 1;
      }
    }

    node_start = node_start + 1;
  }

  pub->publish(pcMsg);
}

#endif

int main(int argc, char **argv)
{
  std::string frame_id, cloud_topic, lidar_ip("192.168.1.100");
  int motor_speed = 15, lidar_port = 2007, filter_size = 1, motor_dir = 1;
  unsigned int motor_speed_get, filter_size_get, motor_dir_get;
  double angle_min = -135.0, angle_max = 135.0;
  double min_range = 0.05, max_range = 30.0;
  bool inverted = false;
  bool save_config = false;

#ifdef ROS_FOUND
  ros::init(argc, argv, "point_cloud_publisher");
  ros::NodeHandle nh;
  ros::NodeHandle nh_private("~");

  nh_private.param<double>("angle_max", angle_max, 135.00);
  nh_private.param<double>("angle_min", angle_min, -135.00);
  nh_private.param<double>("range_max", max_range, 30.0);
  nh_private.param<double>("range_min", min_range, 0.05);
  nh_private.param<bool>("inverted", inverted, false);
  nh_private.param<int>("motor_speed", motor_speed, 20);
  nh_private.param<int>("filter_size", filter_size, 1);
  nh_private.param<int>("motor_dir", motor_dir, 1);
  nh_private.param<std::string>("lidar_ip", lidar_ip, "192.168.1.100");
  nh_private.param<int>("lidar_port", lidar_port, 2007);

  nh_private.param<std::string>("frame_id", frame_id, "pc_frame");
  nh_private.param<std::string>("cloud_topic", cloud_topic, "point_cloud");
  ros::Publisher cloud_pub = nh.advertise<sensor_msgs::PointCloud>(cloud_topic, 50);
#elif ROS2_FOUND
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("oradar_ros"); // create a ROS2 Node

  // declare ros2 param
  node->declare_parameter<std::string>("lidar_ip", lidar_ip);
  node->declare_parameter<int>("lidar_port", lidar_port);
  node->declare_parameter<double>("angle_max", angle_max);
  node->declare_parameter<double>("angle_min", angle_min);
  node->declare_parameter<double>("range_max", max_range);
  node->declare_parameter<double>("range_min", min_range);
  node->declare_parameter<bool>("inverted", inverted);
  node->declare_parameter<int>("motor_speed", motor_speed);
  node->declare_parameter<int>("filter_size", filter_size);
  node->declare_parameter<int>("motor_dir", motor_dir);
  node->declare_parameter<std::string>("frame_id", frame_id);
  node->declare_parameter<std::string>("cloud_topic", cloud_topic);

  // get ros2 param
  node->get_parameter("lidar_ip", lidar_ip);
  node->get_parameter("lidar_port", lidar_port);
  node->get_parameter("angle_max", angle_max);
  node->get_parameter("angle_min", angle_min);
  node->get_parameter("range_max", max_range);
  node->get_parameter("range_min", min_range);
  node->get_parameter("inverted", inverted);
  node->get_parameter("motor_speed", motor_speed);
  node->get_parameter("filter_size", filter_size);
  node->get_parameter("motor_dir", motor_dir);
  node->get_parameter("frame_id", frame_id);
  node->get_parameter("cloud_topic", cloud_topic);

  rclcpp::Publisher<sensor_msgs::msg::PointCloud>::SharedPtr publisher = node->create_publisher<sensor_msgs::msg::PointCloud>(cloud_topic, 50);
#endif

  std::string address_str = lidar_ip;
  std::string port_str = "2007";

  in_addr_t address = htonl(INADDR_NONE);
  in_port_t port = 0;
  try
  {
    address = inet_addr(address_str.c_str());
    if (address == htonl(INADDR_NONE))
      throw std::exception();
    port = htons(std::stoi(port_str));
  }
  catch (...)
  {
    std::cout << "Invalid device address: " << lidar_ip.c_str() << std::endl;
    exit(-1);
  }

  ord_sdk::LidarAddress location(address, port);
  device = std::unique_ptr<ord_sdk::OrdDriver>(new ord_sdk::OrdDriver(location));

  if (motor_speed < 10)
  {
    motor_speed = 10;
  }

  if (motor_speed > 30)
  {
    motor_speed = 30;
  }

#ifdef ROS_FOUND
  while (ros::ok())
#elif ROS2_FOUND
  while (rclcpp::ok())
#endif
  {
    if (device->isOpened() != true)
    {
      if (device->open() == ord_sdk::no_error)
        std::cout << "Device open success" << std::endl;
      else
        std::cout << "Device open fail" << std::endl;
    }

    if (device->trackConnect() != ord_sdk::no_error)
    {
      std::cout << "Device connecting ..." << std::endl;
      sleep(1);
      continue;
    }
    else
    {
      std::cout << "Device connect success" << std::endl;
      break;
    }
  }

  std::string firmware_version;
  if (device->getFirmwareVersion(firmware_version) == ord_sdk::no_error)
  {
    std::cout << "get Firmware version:" << firmware_version.c_str() << std::endl;
  }
  else
    std::cout << "fail: Unable to query device firmware version" << std::endl;

  if (device->getScanSpeed(motor_speed_get) == ord_sdk::no_error)
  {
    std::cout << "get motor speed:" << motor_speed_get << " HZ" << std::endl;
  }
  else
  {
    std::cout << "fail: false to get motor speed" << std::endl;
    return -1;
  }

  if (motor_speed != motor_speed_get)
  {
    save_config = true;
    if (device->setScanSpeed(motor_speed) == ord_sdk::no_error)
    {
      std::cout << "success to set motor speed:" << motor_speed_get << " HZ" << std::endl;
      sleep(1);
    }
    else
    {
      std::cout << "fail: false to set motor speed!" << std::endl;
      return -1;
    }
  }

  if (device->getTailFilterLevel(filter_size_get) == ord_sdk::no_error)
  {
    std::cout << "get filter size " << filter_size_get << std::endl;
  }
  if (filter_size != filter_size_get)
  {
    save_config = true;
    if (device->setTailFilterLevel(filter_size) == ord_sdk::no_error)
    {
      std::cout << "success to set filter size: " << filter_size << std::endl;
      sleep(1);
    }
    else
    {
      std::cout << "fail: false to set filter size!" << std::endl;
      return -1;
    }
  }
  if (device->getScanDirection(motor_dir_get) == ord_sdk::no_error)
  {
    std::cout << "get motor scan dir: " << motor_dir_get << std::endl;
  }
  if (motor_dir_get != motor_dir)
  {
    save_config = true;
    if (device->setScanDirection(motor_dir) == ord_sdk::no_error)
    {
      std::cout << "success to set motor dir: " << motor_dir << std::endl;
      sleep(1);
    }
    else
    {
      std::cout << "fail: false to set motor dir !" << std::endl;
      return -1;
    }
  }

  if (save_config)
  {
    error_t ret = device->applyConfigs();
    if (ret == ord_sdk::no_error)
    {
      std::cout << "success to save config" << std::endl;
      sleep(1);
    }
    else
    {
      std::cout << "fail: save config fail!" << std::endl;
    }
  }

  ord_sdk::error_t result;
  ord_sdk::ScanFrameData scan_frame_data;
#ifdef ROS_FOUND
  ros::Time start_scan_time;
  ros::Time end_scan_time;
  ros::Rate r(motor_speed);
#elif ROS2_FOUND
  rclcpp::Time start_scan_time;
  rclcpp::Time end_scan_time;
  rclcpp::WallRate r(motor_speed);
#endif
  double scan_duration;

  device->enableMeasure();
  device->enabelDataStream();

  std::cout << "get lidar scan data" << std::endl;

#ifdef ROS_FOUND
  start_scan_time = ros::Time::now();
  while (ros::ok())
#elif ROS2_FOUND
  start_scan_time = node->now();
  while (rclcpp::ok())
#endif
  {

    result = device->GrabFullScan(scan_frame_data);
#ifdef ROS_FOUND
    end_scan_time = ros::Time::now();
#elif ROS2_FOUND
    end_scan_time = node->now();
#endif
    if (result == ord_sdk::no_error)
    {
#ifdef ROS_FOUND
      scan_duration = (end_scan_time - start_scan_time).toSec();
      publish_msg(&cloud_pub, scan_frame_data, start_scan_time, scan_duration, frame_id,
                  inverted, angle_min, angle_max, min_range, max_range);

      ros::spinOnce();
#elif ROS2_FOUND
      scan_duration = (end_scan_time.seconds() - start_scan_time.seconds());
      publish_msg(publisher, scan_frame_data, start_scan_time, scan_duration, frame_id,
                  inverted, angle_min, angle_max, min_range, max_range);
#endif
    }
    
    start_scan_time = end_scan_time;
    r.sleep();
  }

  device->disableDataStream();
  device->close();
#ifdef ROS_FOUND
  ros::shutdown();
#elif ROS2_FOUND
  rclcpp::shutdown();
#endif

  return 0;
}
