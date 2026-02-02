#include "nav_toroom/at_targetpose_condition.h"

AtTargetRoomCondition::AtTargetRoomCondition(const std::string& name, const BT::NodeConfiguration& config)
  : BT::ConditionNode(name, config),
    tf_listener_(tf_buffer_)
{
  get_room_pose_client_ = nh_.serviceClient<agrobot_bt_manager::get_roompose>("/get_room_pose");
  last_room_name_ = "";
}

BT::PortsList AtTargetRoomCondition::providedPorts()
{
  return {
    BT::InputPort<std::string>("nav_target_room")
  };
}

BT::NodeStatus AtTargetRoomCondition::tick()
{
  std::string room_name;

  if (!getInput("nav_target_room", room_name)) {
    return BT::NodeStatus::FAILURE;
  }

  //  只有房间名发生变化时才触发位置判断
  if (room_name == last_room_name_) {
    ROS_INFO("AtTargetRoomCondition: room [%s] already checked, skipping", room_name.c_str());
    return BT::NodeStatus::FAILURE;
  }

  // 记录当前判断过的房间名
  last_room_name_ = room_name;

  // 调用 get_room_pose 服务
  agrobot_bt_manager::get_roompose srv;
  srv.request.room_name = room_name;

  if (!get_room_pose_client_.call(srv) || !srv.response.success) {
    ROS_ERROR_STREAM("Failed to get room pose for [" << room_name << "]: " << srv.response.message);
    return BT::NodeStatus::FAILURE;
  }

  double target_x = srv.response.x;
  double target_y = srv.response.y;

  geometry_msgs::TransformStamped tf;
  try {
    tf = tf_buffer_.lookupTransform("map", "base_link", ros::Time(0), ros::Duration(0.5));
  } catch (tf2::TransformException& ex) {
    ROS_WARN("TF lookup failed: %s", ex.what());
    return BT::NodeStatus::FAILURE;
  }

  double robot_x = tf.transform.translation.x;
  double robot_y = tf.transform.translation.y;

  double dx = robot_x - target_x;
  double dy = robot_y - target_y;
  double distance = std::hypot(dx, dy);

  ROS_INFO_STREAM("Robot distance to [" << room_name << "] = " << distance);

  if (distance < 0.2) {
    return BT::NodeStatus::SUCCESS;
  } else {
    return BT::NodeStatus::FAILURE;
  }
}
