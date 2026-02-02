#ifndef ORD_SDK_ORD_DRIVER_H_
#define ORD_SDK_ORD_DRIVER_H_

#include "ord/ord_types.h"
#include "ord/ord_driver_net.h"
#include "ord/ord_driver_impl.h"
#include <condition_variable>
#include <thread>
#include <atomic>

namespace ord_sdk
{

  class Impl;

  class OrdDriver
  {
  public:
    OrdDriver(const SocketAddress &sensor);
    virtual ~OrdDriver();
    virtual error_t open();
    bool isOpened() const;
    virtual void close();

    /**
		* @brief Set APT timeout
		* @param[in] timeout  uint:ms
		* @return Setting successfully return 0,otherwise return other values
		*/    
    void setTimeout(int timeout);

    /**
		* @brief Set LiDAR IP Address
		* @param[in] address  ip address info  
		* @return Setting successfully return 0,otherwise return other values
		*/
    error_t setLidarIPAddress(in_addr_t address);
    
    /**
		* @brief Set LiDAR network port number
		* @param[in] port  network port number 
		* @return Setting successfully return 0,otherwise return other values
		*/
    error_t setLidarNetPort(in_port_t port);

    /**
		* @brief Set LiDAR motor speed
		* @param[in] speed  uint:Hz,range:10,15,20,25,30
		* @return Setting successfully return 0,otherwise return other values
		*/
    error_t setScanSpeed(uint32_t speed);
    
    /**
		* @brief Set LiDAR tail filter algorithm level
		* @param[in] level  range:0,1,2,3,4,5
		* @return Setting successfully return 0,otherwise return other values
		*/    
    error_t setTailFilterLevel(uint32_t level);
    
    /**
		* @brief Set LiDAR timestamp
		* @param[in] timestamp uint:us, range:0~3600000000 
		* @return Setting successfully return 0,otherwise return other values
		*/  
    error_t setTimestamp(uint32_t timestamp);
    
    /**
		* @brief Set LiDAR motor spin direction
		* @param[in] direction range value:0(anticlockwise), 1(clockwise)
		* @return Setting successfully return 0,otherwise return other values
		*/  
    error_t setScanDirection(uint32_t direction);

    /**
		* @brief Establish connect with LiDAR 
		* @return connected successfully return 0,otherwise return other values
		*/ 
    error_t trackConnect();

    /**
		* @brief Turn on LiDAR ranging
		* @return turn on successfully return 0,otherwise return other values
		*/ 
    error_t enableMeasure();

    /**
		* @brief Turn off LiDAR ranging
		* @return turn off successfully return 0,otherwise return other values
		*/
    error_t disableMeasure();

    /**
		* @brief Enable LiDAR point cloud data transmission
		* @return enable successfully return 0,otherwise return other values
		*/
    error_t enabelDataStream();

    /**
		* @brief Disable LiDAR point cloud data transmission
		* @return disable successfully return 0,otherwise return other values
		*/
    error_t disableDataStream();

    /**
		* @brief Save parameter configuration information
		* @return successfully return 0,otherwise return other values
		*/
    error_t applyConfigs();
  
    /**
		* @brief Reboot device
		* @return successfully return 0,otherwise return other values
		*/
    error_t deviceReboot();

    /**
		* @brief Get LiDAR IP Address
		* @param[out] address  ip address info  
		* @return Getting successfully return 0,otherwise return other values
		*/
    error_t getLidarIPAddress(in_addr_t &address);

    /**
		* @brief Get LiDAR network port number
		* @param[out] port  network port number 
		* @return Getting successfully return 0,otherwise return other values
		*/
    error_t getLidarNetPort(in_port_t &port);

    /**
		* @brief Get LiDAR motor speed
		* @param[out] speed  uint:Hz,range:10,15,20,25,30
		* @return Getting successfully return 0,otherwise return other values
		*/
    error_t getScanSpeed(uint32_t &speed);

    /**
		* @brief Get LiDAR tail filter algorithm level
		* @param[out] level  range:0,1,2,3,4,5
		* @return Getting successfully return 0,otherwise return other values
		*/  
    error_t getTailFilterLevel(uint32_t &level);

    /**
		* @brief Get LiDAR timestamp
		* @param[out] timestamp uint:us, range:0~3600000000 
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t getTimestamp(uint32_t &timestamp);

    /**
		* @brief Get the real-time speed of the motor
		* @param[out] motor_speed uint:RPM
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t getMotorSpeed(uint32_t &motor_speed);

    /**
		* @brief Get the internal temperature of the LiDAR
		* @param[out] inter_temp uint:0.01 Celsius degree
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t getInternalTemperature(float &inter_temp);

    /**
		* @brief Get synchronization status
		* @param[out] sync_status range value:1(free status), 2(external synchronization status)
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t getSyncStatus(uint32_t &sync_status);

    /**
		* @brief Get the firmware version number
		* @param[out] firmware_version 
		* @return Getting successfully return 0,otherwise return other values
		*/   
    error_t getFirmwareVersion(std::string &firmware_version);

    /**
		* @brief Get the hardware version number
		* @param[out] hardware_version 
		* @return Getting successfully return 0,otherwise return other values
		*/   
    error_t getHardwareVersion(std::string &hardware_version);

    /**
		* @brief Get the SDK version number
		* @param[out] sdk_version 
		* @return Getting successfully return 0,otherwise return other values
		*/   
    error_t getSDKVersion(std::string &sdk_version);

    /**
		* @brief Get LiDAR motor spin direction
		* @param[out] direction range value:0(anticlockwise), 1(clockwise)
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t getScanDirection(uint32_t &direction);
    
	/**
		* @brief Get LiDAR sn
		* @param[out] device_sn
		* @return Getting successfully return 0,otherwise return other values
		*/ 
	error_t getDeviceSN(std::string& device_sn);

    /**
		* @brief Get LiDAR warn info
		* @param[out] warn_code info value: [bit0: motor stall; bit1:temperature abnormal;
		* bit2: high voltage abnormal; bit3:calibration data error; bit4:motor speed abnormal; bit5~7:reserved]
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t getWarnCode(uint8_t &warn_code);

    /**
		* @brief Get LiDAR latest packet of point cloud data, non-blocking
		* @param[out] scan_block_data  scan data
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t GrabOneScan(ScanBlockData &scan_block_data);
  
    /**
		* @brief Get LiDAR latest packet of point cloud data, blocking
		* @param[out] scan_block_data  scan data
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t GrabOneScanBlocking(ScanBlockData &scan_block_data);

    /**
		* @brief Get LiDAR latest circle of point cloud data, non-blocking
		* @param[out] scan_block_data  scan data
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t GrabFullScan(ScanFrameData &scan_frame_data);

    /**
		* @brief Get LiDAR latest circle of point cloud data, blocking
		* @param[out] scan_block_data  scan data
		* @return Getting successfully return 0,otherwise return other values
		*/ 
    error_t GrabFullScanBlocking(ScanFrameData &scan_frame_data);

  protected:
    std::unique_ptr<SocketAddress> sensor_;
    std::unique_ptr<Impl> impl_;

  private:

    std::thread *ParseThread_;
    static void ParseThread(void *param);
    std::atomic<bool> thread_exit_flag_;

    ScanFrameData scan_frame_data_;
    ScanBlockData scan_block_data_;
    std::mutex frame_mutex_;
    std::mutex block_mutex_;
    std::mutex frame_wait_mutex_;
    std::mutex block_wait_mutex_;
    std::condition_variable frame_data_cv_;
    std::condition_variable block_data_cv_;
    bool is_frame_ready_;
    bool is_block_ready_;
    uint8_t frame_begin_;
	uint8_t warn_code_;

    uint32_t FilterLevel_;
    uint32_t MotorSpeed_;
    uint32_t ScanDiret_;
    uint8_t FirstGetInfo_;
    static const int FILTER_WINDOW_SIZE = 7; // Must be odd
    void point_cloud_filter(uint32_t FilterLevel, uint32_t MotorSpeed, std::vector<uint16_t> &distances);
  };

}

#endif
