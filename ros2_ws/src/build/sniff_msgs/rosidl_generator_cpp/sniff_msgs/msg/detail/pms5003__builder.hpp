// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from sniff_msgs:msg/Pms5003.idl
// generated code does not contain a copyright notice

#ifndef SNIFF_MSGS__MSG__DETAIL__PMS5003__BUILDER_HPP_
#define SNIFF_MSGS__MSG__DETAIL__PMS5003__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "sniff_msgs/msg/detail/pms5003__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace sniff_msgs
{

namespace msg
{

namespace builder
{

class Init_Pms5003_sensor_ok
{
public:
  explicit Init_Pms5003_sensor_ok(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  ::sniff_msgs::msg::Pms5003 sensor_ok(::sniff_msgs::msg::Pms5003::_sensor_ok_type arg)
  {
    msg_.sensor_ok = std::move(arg);
    return std::move(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_particles_25um
{
public:
  explicit Init_Pms5003_particles_25um(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  Init_Pms5003_sensor_ok particles_25um(::sniff_msgs::msg::Pms5003::_particles_25um_type arg)
  {
    msg_.particles_25um = std::move(arg);
    return Init_Pms5003_sensor_ok(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_particles_10um
{
public:
  explicit Init_Pms5003_particles_10um(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  Init_Pms5003_particles_25um particles_10um(::sniff_msgs::msg::Pms5003::_particles_10um_type arg)
  {
    msg_.particles_10um = std::move(arg);
    return Init_Pms5003_particles_25um(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_particles_05um
{
public:
  explicit Init_Pms5003_particles_05um(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  Init_Pms5003_particles_10um particles_05um(::sniff_msgs::msg::Pms5003::_particles_05um_type arg)
  {
    msg_.particles_05um = std::move(arg);
    return Init_Pms5003_particles_10um(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_particles_03um
{
public:
  explicit Init_Pms5003_particles_03um(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  Init_Pms5003_particles_05um particles_03um(::sniff_msgs::msg::Pms5003::_particles_03um_type arg)
  {
    msg_.particles_03um = std::move(arg);
    return Init_Pms5003_particles_05um(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_pm10
{
public:
  explicit Init_Pms5003_pm10(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  Init_Pms5003_particles_03um pm10(::sniff_msgs::msg::Pms5003::_pm10_type arg)
  {
    msg_.pm10 = std::move(arg);
    return Init_Pms5003_particles_03um(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_pm25
{
public:
  explicit Init_Pms5003_pm25(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  Init_Pms5003_pm10 pm25(::sniff_msgs::msg::Pms5003::_pm25_type arg)
  {
    msg_.pm25 = std::move(arg);
    return Init_Pms5003_pm10(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_pm1
{
public:
  explicit Init_Pms5003_pm1(::sniff_msgs::msg::Pms5003 & msg)
  : msg_(msg)
  {}
  Init_Pms5003_pm25 pm1(::sniff_msgs::msg::Pms5003::_pm1_type arg)
  {
    msg_.pm1 = std::move(arg);
    return Init_Pms5003_pm25(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

class Init_Pms5003_header
{
public:
  Init_Pms5003_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Pms5003_pm1 header(::sniff_msgs::msg::Pms5003::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Pms5003_pm1(msg_);
  }

private:
  ::sniff_msgs::msg::Pms5003 msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::sniff_msgs::msg::Pms5003>()
{
  return sniff_msgs::msg::builder::Init_Pms5003_header();
}

}  // namespace sniff_msgs

#endif  // SNIFF_MSGS__MSG__DETAIL__PMS5003__BUILDER_HPP_
