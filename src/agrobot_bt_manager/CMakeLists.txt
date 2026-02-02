cmake_minimum_required(VERSION 3.0.2)
project(agrobot_bt_manager)

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  sensor_msgs
  std_msgs
  tf
  serial
  message_generation
  behaviortree_cpp_v3
  pattern_matcher
  RobotCar
)

# find_package(behavior_tree_cpp_v3 REQUIRED)



## System dependencies are found with CMake's conventions
# find_package(Boost REQUIRED COMPONENTS system)


## Uncomment this if the package has a setup.py. This macro ensures
## modules and global scripts declared therein get installed
## See http://ros.org/doc/api/catkin/html/user_guide/setup_dot_py.html
# catkin_python_setup()

################################################
## Declare ROS messages, services and actions ##
################################################

## To declare and build messages, services or actions from within this
## package, follow these steps:
## * Let MSG_DEP_SET be the set of packages whose message types you use in
##   your messages/services/actions (e.g. std_msgs, actionlib_msgs, ...).
## * In the file package.xml:
##   * add a build_depend tag for "message_generation"
##   * add a build_depend and a exec_depend tag for each package in MSG_DEP_SET
##   * If MSG_DEP_SET isn't empty the following dependency has been pulled in
##     but can be declared for certainty nonetheless:
##     * add a exec_depend tag for "message_runtime"
## * In this file (CMakeLists.txt):
##   * add "message_generation" and every package in MSG_DEP_SET to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * add "message_runtime" and every package in MSG_DEP_SET to
##     catkin_package(CATKIN_DEPENDS ...)
##   * uncomment the add_*_files sections below as needed
##     and list every .msg/.srv/.action file to be processed
##   * uncomment the generate_messages entry below
##   * add every package in MSG_DEP_SET to generate_messages(DEPENDENCIES ...)

## Generate messages in the 'msg' folder
add_message_files(
  FILES
  voice_command.msg
  robot_status.msg
  arrived_point.msg
)

## Generate services in the 'srv' folder
add_service_files(
  FILES
  voice_torobot.srv
  get_roompose.srv
)

## Generate actions in the 'action' folder
# add_action_files(
#   FILES
#   Action1.action
#   Action2.action
# )

## Generate added messages and services with any dependencies listed here
generate_messages(
  DEPENDENCIES
  std_msgs
)

################################################
## Declare ROS dynamic reconfigure parameters ##
################################################

## To declare and build dynamic reconfigure parameters within this
## package, follow these steps:
## * In the file package.xml:
##   * add a build_depend and a exec_depend tag for "dynamic_reconfigure"
## * In this file (CMakeLists.txt):
##   * add "dynamic_reconfigure" to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * uncomment the "generate_dynamic_reconfigure_options" section below
##     and list every .cfg file to be processed

## Generate dynamic reconfigure parameters in the 'cfg' folder
# generate_dynamic_reconfigure_options(
#   cfg/DynReconf1.cfg
#   cfg/DynReconf2.cfg
# )

###################################
## catkin specific configuration ##
###################################
## The catkin_package macro generates cmake config files for your package
## Declare things to be passed to dependent projects
## INCLUDE_DIRS: uncomment this if your package contains header files
## LIBRARIES: libraries you create in this project that dependent projects also need
## CATKIN_DEPENDS: catkin_packages dependent projects also need
## DEPENDS: system dependencies of this project that dependent projects also need
catkin_package(
  INCLUDE_DIRS include
  # LIBRARIES agrobot_bt_manager
  # CATKIN_DEPENDS roscpp rospy sensor_msgs std_msgs tf RobotCar
#  DEPENDS system_lib
)

###########
## Build ##
###########

## Specify additional locations of header files
## Your package locations should be listed before other locations
include_directories(
  include
  ${catkin_INCLUDE_DIRS}
  ${behavior_tree_cpp_v3_INCLUDE_DIRS}
  /usr/local/include
)
link_directories(/usr/local/lib)
## Declare a C++ library
# add_library(${PROJECT_NAME}
#   src/${PROJECT_NAME}/agrobot_bt_manager.cpp
# )

## Add cmake target dependencies of the library
## as an example, code may need to be generated before libraries
## either from message generation or dynamic reconfigure
# add_dependencies(${PROJECT_NAME} ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Declare a C++ library
add_library(locate_charge_station
  src/charge_control/locate_charge_station.cpp
)

# ## Add cmake target dependencies of the library
add_dependencies(locate_charge_station ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

# ## Specify libraries to link a library target against
target_link_libraries(locate_charge_station
  ${catkin_LIBRARIES}
)

#检测机器人是否已在目标点
add_library(at_targetpose_condition src/nav_toroom/at_targetpose_condition.cpp)
add_dependencies(at_targetpose_condition ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
target_link_libraries(at_targetpose_condition
  ${catkin_LIBRARIES}
)
#原地等待节点
add_library(wait_attarget_pose src/task_handler/wait_attarget_pose.cpp)
add_dependencies(wait_attarget_pose ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
target_link_libraries(wait_attarget_pose
  ${catkin_LIBRARIES}
)
#发布机器人姿态节点
add_library(setrobotstatus src/task_handler/setrobotstatus.cpp)
add_dependencies(setrobotstatus ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
target_link_libraries(setrobotstatus
  ${catkin_LIBRARIES}
)
#开门节点
add_library(open_door_action src/opendoor/open_door_action.cpp)
add_dependencies(open_door_action ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
target_link_libraries(open_door_action
  ${catkin_LIBRARIES}
)
## Declare a C++ executable for the main node
add_executable(main_bt_runner 
  src/main_bt_runner.cpp
  src/charge_control/locate_charge_station.cpp
  src/opendoor/open_door_action.cpp
  src/nav_toroom/at_targetpose_condition.cpp
  src/task_handler/wait_attarget_pose.cpp
  src/task_handler/setrobotstatus.cpp
  )

# ## Add cmake target dependencies of the executable
add_dependencies(main_bt_runner ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

# ## Specify libraries to link the executable target against
target_link_libraries(main_bt_runner
  ${catkin_LIBRARIES}
  locate_charge_station
  open_door_action
  at_targetpose_condition
  wait_attarget_pose
  setrobotstatus
)

#加载房间坐标节点
add_executable(load_roompose src/load_roompose/load_roompose.cpp)
target_link_libraries(load_roompose ${catkin_LIBRARIES})
#语音命令监听节点
add_executable(voice_command_handler src/voice_control/voice_command_handler.cpp)
target_link_libraries(voice_command_handler ${catkin_LIBRARIES})
# target_include_directories(main_bt_runner PRIVATE
#   ${CMAKE_CURRENT_SOURCE_DIR}/include
# )

#############
## Install ##
#############

# all install targets should use catkin DESTINATION variables
# See http://ros.org/doc/api/catkin/html/adv_user_guide/variables.html

## Mark executable scripts (Python etc.) for installation
## in contrast to setup.py, you can choose the destination
# catkin_install_python(PROGRAMS
#   scripts/my_python_script
#   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
# )

## Mark executables for installation
## See http://docs.ros.org/melodic/api/catkin/html/howto/format1/building_executables.html
# install(TARGETS ${PROJECT_NAME}_node
#   RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
# )

## Mark libraries for installation
## See http://docs.ros.org/melodic/api/catkin/html/howto/format1/building_libraries.html
# install(TARGETS ${PROJECT_NAME}
#   ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   RUNTIME DESTINATION ${CATKIN_GLOBAL_BIN_DESTINATION}
# )

## Mark cpp header files for installation
# install(DIRECTORY include/${PROJECT_NAME}/
#   DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
#   FILES_MATCHING PATTERN "*.h"
#   PATTERN ".svn" EXCLUDE
# )

## Mark other files for installation (e.g. launch and bag files, etc.)
# install(FILES
#   # myfile1
#   # myfile2
#   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
# )

#############
## Testing ##
#############

## Add gtest based cpp test target and link libraries
# catkin_add_gtest(${PROJECT_NAME}-test test/test_agrobot_bt_manager.cpp)
# if(TARGET ${PROJECT_NAME}-test)
#   target_link_libraries(${PROJECT_NAME}-test ${PROJECT_NAME})
# endif()

## Add folders to be run by python nosetests
# catkin_add_nosetests(test)