// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from sniff_msgs:msg/Pms5003.idl
// generated code does not contain a copyright notice

#ifndef SNIFF_MSGS__MSG__DETAIL__PMS5003__STRUCT_H_
#define SNIFF_MSGS__MSG__DETAIL__PMS5003__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in msg/Pms5003 in the package sniff_msgs.
typedef struct sniff_msgs__msg__Pms5003
{
  std_msgs__msg__Header header;
  float pm1;
  float pm25;
  float pm10;
  uint16_t particles_03um;
  uint16_t particles_05um;
  uint16_t particles_10um;
  uint16_t particles_25um;
  bool sensor_ok;
} sniff_msgs__msg__Pms5003;

// Struct for a sequence of sniff_msgs__msg__Pms5003.
typedef struct sniff_msgs__msg__Pms5003__Sequence
{
  sniff_msgs__msg__Pms5003 * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} sniff_msgs__msg__Pms5003__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNIFF_MSGS__MSG__DETAIL__PMS5003__STRUCT_H_
