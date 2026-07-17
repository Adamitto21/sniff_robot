// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from sniff_msgs:msg/Pms5003.idl
// generated code does not contain a copyright notice

#ifndef SNIFF_MSGS__MSG__DETAIL__PMS5003__STRUCT_HPP_
#define SNIFF_MSGS__MSG__DETAIL__PMS5003__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__sniff_msgs__msg__Pms5003 __attribute__((deprecated))
#else
# define DEPRECATED__sniff_msgs__msg__Pms5003 __declspec(deprecated)
#endif

namespace sniff_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Pms5003_
{
  using Type = Pms5003_<ContainerAllocator>;

  explicit Pms5003_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->pm1 = 0.0f;
      this->pm25 = 0.0f;
      this->pm10 = 0.0f;
      this->particles_03um = 0;
      this->particles_05um = 0;
      this->particles_10um = 0;
      this->particles_25um = 0;
      this->sensor_ok = false;
    }
  }

  explicit Pms5003_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->pm1 = 0.0f;
      this->pm25 = 0.0f;
      this->pm10 = 0.0f;
      this->particles_03um = 0;
      this->particles_05um = 0;
      this->particles_10um = 0;
      this->particles_25um = 0;
      this->sensor_ok = false;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _pm1_type =
    float;
  _pm1_type pm1;
  using _pm25_type =
    float;
  _pm25_type pm25;
  using _pm10_type =
    float;
  _pm10_type pm10;
  using _particles_03um_type =
    uint16_t;
  _particles_03um_type particles_03um;
  using _particles_05um_type =
    uint16_t;
  _particles_05um_type particles_05um;
  using _particles_10um_type =
    uint16_t;
  _particles_10um_type particles_10um;
  using _particles_25um_type =
    uint16_t;
  _particles_25um_type particles_25um;
  using _sensor_ok_type =
    bool;
  _sensor_ok_type sensor_ok;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__pm1(
    const float & _arg)
  {
    this->pm1 = _arg;
    return *this;
  }
  Type & set__pm25(
    const float & _arg)
  {
    this->pm25 = _arg;
    return *this;
  }
  Type & set__pm10(
    const float & _arg)
  {
    this->pm10 = _arg;
    return *this;
  }
  Type & set__particles_03um(
    const uint16_t & _arg)
  {
    this->particles_03um = _arg;
    return *this;
  }
  Type & set__particles_05um(
    const uint16_t & _arg)
  {
    this->particles_05um = _arg;
    return *this;
  }
  Type & set__particles_10um(
    const uint16_t & _arg)
  {
    this->particles_10um = _arg;
    return *this;
  }
  Type & set__particles_25um(
    const uint16_t & _arg)
  {
    this->particles_25um = _arg;
    return *this;
  }
  Type & set__sensor_ok(
    const bool & _arg)
  {
    this->sensor_ok = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    sniff_msgs::msg::Pms5003_<ContainerAllocator> *;
  using ConstRawPtr =
    const sniff_msgs::msg::Pms5003_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      sniff_msgs::msg::Pms5003_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      sniff_msgs::msg::Pms5003_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__sniff_msgs__msg__Pms5003
    std::shared_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__sniff_msgs__msg__Pms5003
    std::shared_ptr<sniff_msgs::msg::Pms5003_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Pms5003_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->pm1 != other.pm1) {
      return false;
    }
    if (this->pm25 != other.pm25) {
      return false;
    }
    if (this->pm10 != other.pm10) {
      return false;
    }
    if (this->particles_03um != other.particles_03um) {
      return false;
    }
    if (this->particles_05um != other.particles_05um) {
      return false;
    }
    if (this->particles_10um != other.particles_10um) {
      return false;
    }
    if (this->particles_25um != other.particles_25um) {
      return false;
    }
    if (this->sensor_ok != other.sensor_ok) {
      return false;
    }
    return true;
  }
  bool operator!=(const Pms5003_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Pms5003_

// alias to use template instance with default allocator
using Pms5003 =
  sniff_msgs::msg::Pms5003_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace sniff_msgs

#endif  // SNIFF_MSGS__MSG__DETAIL__PMS5003__STRUCT_HPP_
