
# MS500 SDK Basic Introduction
The MS500 SDK is a software development kit designed specifically for the Oradar MS500 LIDAR product. With the MS500 SDK, users can quickly connect to the Oradar MS500 LIDAR and receive LIDAR point cloud data.

# Operational requirements
- Linux system: Ubuntu 14.04 LTS, Ubuntu 16.04 LTS, Ubuntu 18.04 LTS
- Windows 7/10
- C++ 11 compiler
- CMake, version 3.5 or higher

# Compilation methods

Use following commands in Linux:
```
cd sdk
mkdir build
cd build
cmake ..
make
```
Use following commands in Windows:

(Here is a windows 10 system, the compiler is QT MinGW for example. You need to import the compiler installation path into the system environment variable)
```
cd sdk
mkdir build
cd build
cmake -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release ..
mingw32-make -j8
```

Generate `ord_sdk.a` library file, `scan_frame_test`executable files.


# API Description of SDK Main Functions
|Function name| Function introduction|
|---------|---------------|
|open| Open the LiDAR  |
|close| Close the LiDAR |
|isOpened| Query whether it is in the open status |
|trackConnect           | Establish connect with LiDAR |
|enableMeasure   | Turn on LiDAR ranging |
|disableMeasure          | Turn off LiDAR ranging |
|enabelDataStream  | Enable LiDAR point cloud data transmission |
|disableDataStream      | Disable LiDAR point cloud data transmission |
|GrabOneScan      | Get LiDAR latest packet of point cloud data, non-blocking|
|GrabOneScanBlocking          | Get LiDAR latest packet of point cloud data, blocking |
|GrabFullScan      | Get LiDAR latest circle of point cloud data, non-blocking |
|GrabFullScanBlocking          | Get LiDAR latest circle of point cloud data, blocking |
|setLidarIPAddress    | Set LiDAR IP Address|
|getLidarIPAddress              | Get LiDAR IP Address |
|setLidarNetPort              | Set LiDAR net port number |
|getLidarNetPort              | Get LiDAR net port number |
|setScanSpeed | Set LiDAR motor speed|
|getScanSpeed | Get LiDAR motor speed |
|setTailFilterLevel | Set LiDAR filter level,set range: 0,1,2,3,4,5 |
|getTailFilterLevel | Get LiDAR filter level |
|setTimestamp | Set LiDAR timestamp |
|getTimestamp | Get LiDAR timestamp |
|applyConfigs | Save parameter configuration information|
|deviceReboot | Reboot device |
|getFirmwareVersion | Get the firmware version number |
|getHardwareVersion | Get the hardware version number |
|getSDKVersion | Get the SDK version number |
|getMotorSpeed | Get the real-time speed of the motor, uint:RPM|
|getInternalTemperature | Get the internal temperature of the LiDAR, uint:0.01 Celsius degree|
|getSyncStatus | Get synchronization status|
|setTimeout | Set API timeout,uint:ms |


# Sample Usage Instructions

Linux:

Connect the MS500 LIDAR device to Ubuntu system through a network cable. Open the terminal under Ubuntu system, and set the corresponding NIC IP to "192.168.1.10". Then, execute SDK Sample, and enter the following command：

```
cd sdk/build
./scan_frame_test
```

Windows:

Connect the MS500 LiDAR device to Windows system via network cable, and set the corresponding NIC IP to "192.168.1.10" in the network settings. And then , click the "scan_frame_test.exe".

