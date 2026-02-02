#include "ord/ord_driver.h"
#include <algorithm>
#include <cstring>
#include <iostream>

namespace ord_sdk
{

  OrdDriver::OrdDriver(const SocketAddress &sensor)
      : impl_(new Impl())
  {
    if (typeid(sensor) == typeid(LidarAddress))
      sensor_ = std::unique_ptr<LidarAddress>(new LidarAddress((const LidarAddress &)sensor));

    FilterLevel_ = 0;
    MotorSpeed_ = 0;
    FirstGetInfo_ = 0;
    ScanDiret_ = 0;

    frame_begin_ = 0;
    is_frame_ready_ = false;
    is_block_ready_ = false;
    ParseThread_ = NULL;
  }

  OrdDriver::~OrdDriver()
  {
    if (impl_ && impl_->isOpened())
      impl_->close();
  }

  error_t OrdDriver::open()
  {
    return impl_->open(*sensor_);
  }

  bool OrdDriver::isOpened() const
  {
    return impl_->isOpened();
  }

  void OrdDriver::close()
  {
    impl_->close();
  }

  void OrdDriver::setTimeout(int timeout)
  {
    impl_->setTimeout(timeout);
  }

  error_t OrdDriver::setLidarIPAddress(in_addr_t address)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    content.resize(4);
    *(uint32_t *)(content.data()) = htonl(address);
    impl_->GnerateProtocolFrame(set_lidar_ip, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::setLidarNetPort(in_port_t port)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    content.resize(4);
    *(uint16_t *)(content.data()) = htons(port);
    impl_->GnerateProtocolFrame(set_lidar_port, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::setTailFilterLevel(uint32_t level)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    content.resize(4);
    *(uint32_t *)(content.data()) = htonl(level);
    impl_->GnerateProtocolFrame(set_filter_level, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      FilterLevel_ = level;
    }
    return result;
  }

  error_t OrdDriver::setTimestamp(uint32_t timestamp)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    content.resize(4);
    *(uint32_t *)(content.data()) = htonl(timestamp);
    impl_->GnerateProtocolFrame(set_timestamp, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::setScanSpeed(uint32_t speed)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    content.resize(4);
    *(uint32_t *)(content.data()) = htonl(speed);
    impl_->GnerateProtocolFrame(set_scan_speed, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      MotorSpeed_ = speed;
      frame_begin_ = 0;
    }
    return result;
  }

  error_t OrdDriver::trackConnect()
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    uint32_t CmdCode = 0x12345678;
    content.resize(4);
    *(uint32_t *)content.data() = htonl(CmdCode);
    impl_->GnerateProtocolFrame(set_track_connect, request, content);
    result = impl_->DealProtocolData(std::move(request), response);

    if (result == no_error)
    {
      if (FirstGetInfo_ == 0)
      {
        error_t get_scan_ret = getScanDirection(ScanDiret_);
        error_t ret = getTailFilterLevel(FilterLevel_);
        if (ret == error_t::no_error)
        {
          ret = getScanSpeed(MotorSpeed_);
          if ((ret == error_t::no_error) && (get_scan_ret == error_t::no_error))
          {
            FirstGetInfo_ = 1;
          }
        }
      }
      thread_exit_flag_ = false;
      if(ParseThread_ == NULL)
        ParseThread_ = new std::thread(ParseThread, this);
    }
    return result;
  }

  error_t OrdDriver::enableMeasure()
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    uint32_t CmdCode = 0x01;
    content.resize(4);
    *(uint32_t *)content.data() = htonl(CmdCode);
    impl_->GnerateProtocolFrame(set_measure_onoff, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::disableMeasure()
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    uint32_t CmdCode = 0x00;
    content.resize(4);
    *(uint32_t *)content.data() = htonl(CmdCode);
    impl_->GnerateProtocolFrame(set_measure_onoff, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::enabelDataStream()
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    uint32_t CmdCode = 0x01;
    content.resize(4);
    *(uint32_t *)content.data() = htonl(CmdCode);
    impl_->GnerateProtocolFrame(set_stream_onoff, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::disableDataStream()
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    uint32_t CmdCode = 0x00;
    content.resize(4);
    *(uint32_t *)content.data() = htonl(CmdCode);
    impl_->GnerateProtocolFrame(set_stream_onoff, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::setScanDirection(uint32_t direction)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    content.resize(4);
    *(uint32_t *)(content.data()) = htonl(direction);
    impl_->GnerateProtocolFrame(set_scan_direction, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      ScanDiret_ = direction;
      frame_begin_ = 0;
    }
    return result;
  }

  error_t OrdDriver::applyConfigs()
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    uint32_t CmdCode = 0x00;
    content.resize(4);
    *(uint32_t *)content.data() = htonl(CmdCode);
    impl_->GnerateProtocolFrame(set_parameter_save, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::deviceReboot()
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    uint32_t CmdCode = 0x00;
    content.resize(4);
    *(uint32_t *)content.data() = htonl(CmdCode);
    impl_->GnerateProtocolFrame(set_device_reboot, request, content);
    result = impl_->DealProtocolData(std::move(request), response);
    return result;
  }

  error_t OrdDriver::getLidarIPAddress(in_addr_t &address)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_lidar_ip, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      address = ntohl(*(uint32_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getLidarNetPort(in_port_t &port)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_lidar_port, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      port = ntohs(*(uint16_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getScanSpeed(uint32_t &speed)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_scan_speed, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      speed = ntohl(*(uint32_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getTailFilterLevel(uint32_t &level)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_filter_level, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      level = ntohl(*(uint32_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getTimestamp(uint32_t &timestamp)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_timestamp, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      timestamp = ntohl(*(uint32_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getMotorSpeed(uint32_t &motor_speed)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_motor_speed, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      motor_speed = ntohl(*(uint32_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getInternalTemperature(float &inter_temp)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_temperature, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      inter_temp = *(float *)response.data();
    }
    return result;
  }

  error_t OrdDriver::getSyncStatus(uint32_t &sync_status)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;
    impl_->GnerateProtocolFrame(get_sync_status, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      sync_status = ntohl(*(uint32_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getFirmwareVersion(std::string &firmware_version)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_firmware_version, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      firmware_version.assign((char *)response.data(), 16);
    }
    return result;
  }

  error_t OrdDriver::getHardwareVersion(std::string &hardware_version)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_hardware_version, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      hardware_version.assign((char *)response.data(), 16);
    }
    return result;
  }

  error_t OrdDriver::getSDKVersion(std::string &sdk_version)
  {

    error_t result = no_error;

    sdk_version = "v1.4.0";

    return result;
  }

  error_t OrdDriver::getScanDirection(uint32_t &direction)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_scan_direction, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      direction = ntohl(*(uint32_t *)response.data());
    }
    return result;
  }

  error_t OrdDriver::getDeviceSN(std::string &device_sn)
  {
    error_t result = no_error;
    std::vector<uint8_t> request, response, content;

    impl_->GnerateProtocolFrame(get_device_sn, request, content);

    result = impl_->DealProtocolData(std::move(request), response);
    if (result == no_error)
    {
      device_sn.assign((char *)response.data(), 16);
    }
    return result;
  }

  error_t OrdDriver::getWarnCode(uint8_t &warn_code)
  {
    warn_code = warn_code_;
    return no_error;
  }

  error_t OrdDriver::GrabOneScan(ScanBlockData &scan_block_data)
  {
    if (is_block_ready_)
    {
      block_mutex_.try_lock();
      scan_block_data = scan_block_data_;
      block_mutex_.unlock();
      is_block_ready_ = false;
      return no_error;
    }

    return timed_out;
  }

  error_t OrdDriver::GrabOneScanBlocking(ScanBlockData &scan_block_data)
  {
    std::unique_lock<std::mutex> lock(block_wait_mutex_);
    std::cv_status status = block_data_cv_.wait_for(lock, std::chrono::milliseconds(1000));

    if ((status == std::cv_status::no_timeout) && is_block_ready_)
    {
      block_mutex_.try_lock();
      scan_block_data = scan_block_data_;
      block_mutex_.unlock();
      is_block_ready_ = false;
      return error_t::no_error;
    }
    else
    {
      return error_t::timed_out;
    }
  }

  error_t OrdDriver::GrabFullScan(ScanFrameData &scan_frame_data)
  {
    if (is_frame_ready_)
    {
      frame_mutex_.try_lock();
      scan_frame_data = scan_frame_data_;
      frame_mutex_.unlock();
      is_frame_ready_ = false;

      return no_error;
    }
    return timed_out;
  }

  error_t OrdDriver::GrabFullScanBlocking(ScanFrameData &scan_frame_data)
  {
    std::unique_lock<std::mutex> lock(frame_wait_mutex_);
    std::cv_status status = frame_data_cv_.wait_for(lock, std::chrono::milliseconds(1000));

    if ((status == std::cv_status::no_timeout) && is_frame_ready_)
    {
      frame_mutex_.try_lock();
      scan_frame_data = scan_frame_data_;
      frame_mutex_.unlock();
      is_frame_ready_ = false;
      return error_t::no_error;
    }
    else
    {
      return error_t::timed_out;
    }
  }

  void OrdDriver::ParseThread(void *param)
  {
    OrdDriver *handle = (OrdDriver *)param;
    ScanFrameData scan_frame_data;
    ScanBlockData scan_block_data;
    uint8_t index = 0;

    while (!handle->thread_exit_flag_.load())
    {
      if (handle->FirstGetInfo_ == 0)
      {
        error_t get_scan_ret = handle->getScanDirection(handle->ScanDiret_);
        error_t ret = handle->getTailFilterLevel(handle->FilterLevel_);
        if (ret == error_t::no_error)
        {
          ret = handle->getScanSpeed(handle->MotorSpeed_);
          if ((ret == error_t::no_error) && (get_scan_ret == error_t::no_error))
          {
            handle->FirstGetInfo_ = 1;
          }
        }
      }

      std::vector<uint8_t> temp_data;
      error_t result = handle->impl_->waitScanData(temp_data);
      if (result == no_error)
      {
        if (temp_data.size() > 0)
        {
          const PointCloudPacket *pc_packet = reinterpret_cast<const PointCloudPacket *>(temp_data.data() + sizeof(ordFrameHead));
          uint8_t block_scan_type = pc_packet->data_type;
          handle->warn_code_ = pc_packet->warn_code;            //告警码
          uint32_t block_length = 0;
          switch (block_scan_type)
          {
          case LASER_SCAN_BLOCK_TYPE_10HZ:
            block_length = LASER_SCAN_BLOCK_LENGTH_10HZ;
            break;
          case LASER_SCAN_BLOCK_TYPE_15HZ:
            block_length = LASER_SCAN_BLOCK_LENGTH_15HZ;
            break;
          case LASER_SCAN_BLOCK_TYPE_20HZ:
            block_length = LASER_SCAN_BLOCK_LENGTH_20HZ;
            break;
          case LASER_SCAN_BLOCK_TYPE_25HZ:
            block_length = LASER_SCAN_BLOCK_LENGTH_25HZ;
            break;
          case LASER_SCAN_BLOCK_TYPE_30HZ:
            block_length = LASER_SCAN_BLOCK_LENGTH_30HZ;
            break;
          }
          scan_block_data.block_id = pc_packet->block_num;
          scan_block_data.timestamp = ntohl(pc_packet->timestamp);
          scan_block_data.frame_cnt = ntohs(pc_packet->frame_count);
          scan_block_data.sync_mode = pc_packet->sync_mode;
          scan_block_data.layers.resize(1);
          scan_block_data.layers[0].ranges.resize(block_length);
          scan_block_data.layers[0].intensities.resize(block_length);
          for (int i = 0; i < block_length; i++)
          {
            scan_block_data.layers[0].ranges[i] = ntohs(*(uint16_t *)(pc_packet->pc_data + 3 * i));
            scan_block_data.layers[0].intensities[i] = *(pc_packet->pc_data + 3 * i + 2);
          }
        }

        // block
        handle->block_mutex_.try_lock();
        handle->scan_block_data_ = scan_block_data;
        handle->block_mutex_.unlock();
        handle->is_block_ready_ = true;
        std::lock_guard<std::mutex> block_lock(handle->block_wait_mutex_);
        handle->block_data_cv_.notify_one();

        int count = scan_block_data.layers[0].ranges.size();
        uint8_t _id = scan_block_data.block_id;
        // std::cout << "_id: " <<std::to_string(_id) << std::endl;

        if ((handle->frame_begin_ == 0) && ((handle->ScanDiret_ == 0 && _id == 1) ||
                                            (handle->ScanDiret_ == 1 && _id == 6)))
        {
          handle->frame_begin_ = 1;
          scan_frame_data.timestamp = scan_block_data.timestamp;
          scan_frame_data.layers.resize(1);
          scan_frame_data.layers[0].ranges.resize(count * 6);
          scan_frame_data.layers[0].intensities.resize(count * 6);
        }

        if (handle->frame_begin_)
        {
          for (int i = 0; i < count; i++)
          {
            scan_frame_data.layers[0].ranges[(_id - 1) * count + i] = scan_block_data.layers[0].ranges[i];
            scan_frame_data.layers[0].intensities[(_id - 1) * count + i] = scan_block_data.layers[0].intensities[i];
          }
          index++;
          if (index >= 6) // frame
          {
            index = 0;
            handle->frame_begin_ = 0;

            if ((handle->ScanDiret_ == 0 && _id == 6) ||
                (handle->ScanDiret_ == 1 && _id == 1))
            {
              handle->point_cloud_filter(handle->FilterLevel_, handle->MotorSpeed_, scan_frame_data.layers[0].ranges);

              handle->frame_mutex_.try_lock();
              handle->scan_frame_data_ = scan_frame_data;
              handle->frame_mutex_.unlock();
              handle->is_frame_ready_ = true;

              std::lock_guard<std::mutex> frame_lock(handle->frame_wait_mutex_);
              handle->frame_data_cv_.notify_one();
            }
          }
        }
      }
    }
  }

  void OrdDriver::point_cloud_filter(uint32_t FilterLevel, uint32_t MotorSpeed, std::vector<uint16_t> &distances)
  {
    uint16_t SumLeftAbnormal = 0;
    uint16_t SumRightAbnormal = 0;
    int32_t Neighbors_ = 0;
    int32_t PointNumThreshold = 0;
    float TanAngleThreshold = 0;
    float AngleResSin = 0;
    float AngleResCos = 0;
    double TanAngle = 0;
    uint16_t abnormal_point_diff = 25;
    uint16_t PointDistanceCmp = 0;
    uint16_t cur_distance = 0;
    uint16_t diff_1, diff_2;
    uint16_t left_aver = 0, right_aver = 0;
    uint16_t aver_thr = 30;
    int count = distances.size();

    std::vector<uint16_t> temp_distance_data;

    if (count < FILTER_WINDOW_SIZE)
    {
      return;
    }

    if (FilterLevel == 0)
    {
      return;
    }
    if ((MotorSpeed != 10) && (MotorSpeed != 15) && (MotorSpeed != 20) && (MotorSpeed != 25) && (MotorSpeed != 30))
    {
      return;
    }

    // std::cout << "FilterLevel:" << FilterLevel << "MotorSpeed:" << MotorSpeed << "count:" << count << std::endl;
    temp_distance_data.resize(count);
    std::copy(distances.begin(), distances.end(), temp_distance_data.begin());

    switch (FilterLevel)
    {
    case 1:
    {
      TanAngleThreshold = 0.03492076949175;
      Neighbors_ = 0;
      PointNumThreshold = 3;
      break;
    }
    case 2:
    {
      TanAngleThreshold = 0.052407779283041;
      Neighbors_ = 0;
      PointNumThreshold = 3;
      break;
    }
    case 3:
    {
      TanAngleThreshold = 0.052407779283041;
      Neighbors_ = 1;
      PointNumThreshold = 3;
      break;
    }
    case 4:
    {
      TanAngleThreshold = 0.096289048197539; // 0.096289048197539;//0.158384440324536;
      Neighbors_ = 0;
      PointNumThreshold = 3;
      break;
    }
    case 5:
    {
      TanAngleThreshold = 0.096289048197539; // 0.158384440324536;
      Neighbors_ = 1;
      PointNumThreshold = 3;
      break;
    }
    default:
    {
      TanAngleThreshold = 0;
      break;
    }
    }

    switch (MotorSpeed)
    {
    case 10:
    {
      AngleResSin = -0.002073449665673;
      AngleResCos = 0.999997850400932;
      abnormal_point_diff = 15;
      break;
    }
    case 15:
    {
      AngleResSin = -0.003110171712830;
      AngleResCos = 0.999995163404262;
      abnormal_point_diff = 30;
      break;
    }
    case 20:
    {
      AngleResSin = -0.004146890417175;
      AngleResCos = 0.999991401612968;
      abnormal_point_diff = 25;
      break;
    }
    case 25:
    {
      AngleResSin = -0.005183604664443;
      AngleResCos = 0.999986565031092;
      abnormal_point_diff = 35;
      break;
    }
    case 30:
    {
      AngleResSin = -0.006220313340373;
      AngleResCos = 0.999980653663833;
      abnormal_point_diff = 40;
      break;
    }
    default:
    {
      break;
    }
    }

    for (int i = (FILTER_WINDOW_SIZE / 2); i < (count - (FILTER_WINDOW_SIZE / 2)); i++)
    {
      cur_distance = temp_distance_data[i];
      if (cur_distance > temp_distance_data[i + 1])
      {
        diff_1 = cur_distance - temp_distance_data[i + 1];
      }
      else
      {
        diff_1 = temp_distance_data[i + 1] - cur_distance;
      }

      if (cur_distance > temp_distance_data[i - 1])
      {
        diff_2 = cur_distance - temp_distance_data[i - 1];
      }
      else
      {
        diff_2 = temp_distance_data[i - 1] - cur_distance;
      }

      if ((diff_1 < abnormal_point_diff) && (diff_2 < abnormal_point_diff))
      {
        if (cur_distance > 500)
        {
          continue;
        }
      }

      int half_window = FILTER_WINDOW_SIZE / 2;

      int l_temp = 0, r_temp = 0;
      for (int n = (i - half_window); n < i + half_window + 1; n++)
      {
        if (n < (i + half_window))
          l_temp = distances[n];
        else if (n > i + half_window)
          r_temp = distances[n];
      }

      left_aver = l_temp / half_window;
      right_aver = r_temp / half_window;

      for (int pos = (i - half_window); pos < i + half_window + 1; pos++)
      {
        if (pos == i || cur_distance == 0)
        {
          continue;
        }

        PointDistanceCmp = temp_distance_data[pos];
        TanAngle = (cur_distance * AngleResSin) / (PointDistanceCmp - cur_distance * AngleResCos);
        if ((TanAngle < TanAngleThreshold) && (TanAngle > ((-1) * TanAngleThreshold)))
        {
          if (pos < i)
            SumLeftAbnormal++;
          else
            SumRightAbnormal++;
        }

        if ((SumLeftAbnormal >= PointNumThreshold) || (SumRightAbnormal >= PointNumThreshold))
        {
          if ((abs(distances[i] - left_aver) > aver_thr) || (abs(distances[i] - right_aver) > aver_thr))
          {
            for (int num = ((-1) * Neighbors_); num <= Neighbors_; num++)
            {
              distances[i + num] = 0;
            }
          }

          break;
        }
      }

      SumLeftAbnormal = 0;
      SumRightAbnormal = 0;
    }
  }

}
