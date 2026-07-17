// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from sniff_msgs:msg/Pms5003.idl
// generated code does not contain a copyright notice

#ifndef SNIFF_MSGS__MSG__DETAIL__PMS5003__TRAITS_HPP_
#define SNIFF_MSGS__MSG__DETAIL__PMS5003__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "sniff_msgs/msg/detail/pms5003__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace sniff_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const Pms5003 & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: pm1
  {
    out << "pm1: ";
    rosidl_generator_traits::value_to_yaml(msg.pm1, out);
    out << ", ";
  }

  // member: pm25
  {
    out << "pm25: ";
    rosidl_generator_traits::value_to_yaml(msg.pm25, out);
    out << ", ";
  }

  // member: pm10
  {
    out << "pm10: ";
    rosidl_generator_traits::value_to_yaml(msg.pm10, out);
    out << ", ";
  }

  // member: particles_03um
  {
    out << "particles_03um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_03um, out);
    out << ", ";
  }

  // member: particles_05um
  {
    out << "particles_05um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_05um, out);
    out << ", ";
  }

  // member: particles_10um
  {
    out << "particles_10um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_10um, out);
    out << ", ";
  }

  // member: particles_25um
  {
    out << "particles_25um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_25um, out);
    out << ", ";
  }

  // member: sensor_ok
  {
    out << "sensor_ok: ";
    rosidl_generator_traits::value_to_yaml(msg.sensor_ok, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Pms5003 & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: pm1
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pm1: ";
    rosidl_generator_traits::value_to_yaml(msg.pm1, out);
    out << "\n";
  }

  // member: pm25
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pm25: ";
    rosidl_generator_traits::value_to_yaml(msg.pm25, out);
    out << "\n";
  }

  // member: pm10
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pm10: ";
    rosidl_generator_traits::value_to_yaml(msg.pm10, out);
    out << "\n";
  }

  // member: particles_03um
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "particles_03um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_03um, out);
    out << "\n";
  }

  // member: particles_05um
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "particles_05um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_05um, out);
    out << "\n";
  }

  // member: particles_10um
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "particles_10um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_10um, out);
    out << "\n";
  }

  // member: particles_25um
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "particles_25um: ";
    rosidl_generator_traits::value_to_yaml(msg.particles_25um, out);
    out << "\n";
  }

  // member: sensor_ok
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sensor_ok: ";
    rosidl_generator_traits::value_to_yaml(msg.sensor_ok, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Pms5003 & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace sniff_msgs

namespace rosidl_generator_traits
{

[[deprecated("use sniff_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const sniff_msgs::msg::Pms5003 & msg,
  std::ostream & out, size_t indentation = 0)
{
  sniff_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use sniff_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const sniff_msgs::msg::Pms5003 & msg)
{
  return sniff_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<sniff_msgs::msg::Pms5003>()
{
  return "sniff_msgs::msg::Pms5003";
}

template<>
inline const char * name<sniff_msgs::msg::Pms5003>()
{
  return "sniff_msgs/msg/Pms5003";
}

template<>
struct has_fixed_size<sniff_msgs::msg::Pms5003>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<sniff_msgs::msg::Pms5003>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<sniff_msgs::msg::Pms5003>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SNIFF_MSGS__MSG__DETAIL__PMS5003__TRAITS_HPP_
