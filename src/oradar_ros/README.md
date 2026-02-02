# ORADAR ROS package
ORADAR ROS包用于连接Oradar MS500激光雷达，此ROS包支持ROS和ROS2环境。其中ROS支持 Indigo，Kinetic，Melodic等ROS版本；ROS2支持Ubuntu 18.04 ROS2 Dashing、Eloquent, Ubuntu 20.04 ROS2 Foxy版本。

## 使用方法： 
1. 在系统中安装ROS环境，具体安装方法参考下面链接：  
   ROS安装链接：http://wiki.ros.org/kinetic/Installation/Ubuntu 

   ROS2安装链接：https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html(ROS2 Foxy版本)

   **请不要在一台电脑上同时安装ROS和ROS2，以避免可能的版本冲突和手工安装其他库的麻烦**
  
2. 将oradar_ros源码复制到ros工作目录下的src目录，并修改相应文件

   ```shell
   mkdir -p ~/lidar_ros_ws/src
   cp -ar oradar_ros ~/lidar_ros_ws/src/
   ```
   (1) 当使用ROS时，需要打开oradar_ros源码根目录下的*CMakeLists.txt*文件，将文件顶部的变量**COMPILE_METHOD**改为**CATKIN**，

   ```cmake
   #=======================================
   # Compile setup (ORIGINAL,CATKIN,COLCON)
   #=======================================
   set(COMPILE_METHOD CATKIN)
   ```

   然后把*package_ros1.xml*文件复制一份，命名为为*package.xml*。

   (2) 当使用ROS2时，需要打开oradar_ros源码根目录下的*CMakeLists.txt*文件，将文件顶部的变量**COMPILE_METHOD**改为**COLCON**，

   ```cmake
   #=======================================
   # Compile setup (ORIGINAL,CATKIN,COLCON)
   #=======================================
   set(COMPILE_METHOD COLCON)
   ```

   然后把*package_ros2.xml*文件复制一份，命名为*package.xml*。
3. 编译工程、设置环境变量

   **当环境是ROS时：**

   ```shell
   cd ~/lidar_ros_ws
   catkin_make
   source devel/setup.bash
   ```

   **当环境是ROS2时：**

   ```
   cd ~/lidar_ros_ws
   colcon build
   source install/setup.bash
   ```

4. 配置Ubuntu系统IP  
    与雷达连接的网卡IP： 默认雷达IP为192.168.1.100, Ubuntu系统IP可配置为192.168.1.10（不能和雷达IP一样）
  
5. 配置雷达参数  
  
    打开oradar_ros/launch/下的launch文件进行参数配置
    参数说明：
    1）device_model雷达设备型号，default=MS500
    2）frame_id 雷达id，default=laser_frame  
    3）scan_topic 雷达的topic名称，default=scan  
    4）angle_min 最小角度，单位度，取值范围 [-135,135],default=-135，即-135度  
    5）angle_max 最大角度，单位度，取值范围 [-135,135],default=135，即135度   
    6）range_min 最小距离，单位米，default=0.05   
    7）range_max 最大距离，单位米，default=30.0  
    8）inverted 是否设置倒装，取值范围true，false。default=false  
    9）motor_speed 雷达转速，单位Hz，取值范围为10,15,20,25,30。default=15Hz  
    10）lidar_ip 所要连接的雷达IP地址，默认为192.168.1.100  
    11）lidar_port 所要连接的雷达端口号，默认为2007  
    12）filter_size 雷达滤波等级，取值范围0,1,2,3,4,5。default=1
  13) motor_dir 雷达电机旋转方向，取值范围0(逆时针)，1(顺时针)。default=0

6. 启动Oradar ROS节点

   **当环境是ROS时**：

   1. 发布LaserScan消息
   ```shell
   roslaunch oradar_ros ms500_scan.launch
   或者
   roslaunch oradar_ros ms500_scan_view.launch (使用rviz显示) 
   ```
   2. 发布PointCloud消息
   ```shell
   roslaunch oradar_ros ms500_pointcloud.launch
   或者
   roslaunch oradar_ros ms500_pointcloud_view.launch (使用rviz显示) 
   ```

   **当环境是ROS2时**：

   1. 发布LaserScan消息
   ```shell
   ros2 launch oradar_ros ms500_scan.launch.py
   或者
   ros2 launch oradar_ros ms500_scan_view.launch.py（使用rviz2显示）
   ```
   2. 发布PointCloud消息
   ```shell
   ros2 launch oradar_ros ms500_pointcloud.launch.py
   或者
   ros2 launch oradar_ros ms500_pointcloud_view.launch.py（使用rviz2显示）
   ```

