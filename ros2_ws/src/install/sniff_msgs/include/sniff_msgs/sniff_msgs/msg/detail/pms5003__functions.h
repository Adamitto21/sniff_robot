// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from sniff_msgs:msg/Pms5003.idl
// generated code does not contain a copyright notice

#ifndef SNIFF_MSGS__MSG__DETAIL__PMS5003__FUNCTIONS_H_
#define SNIFF_MSGS__MSG__DETAIL__PMS5003__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "sniff_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "sniff_msgs/msg/detail/pms5003__struct.h"

/// Initialize msg/Pms5003 message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * sniff_msgs__msg__Pms5003
 * )) before or use
 * sniff_msgs__msg__Pms5003__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
bool
sniff_msgs__msg__Pms5003__init(sniff_msgs__msg__Pms5003 * msg);

/// Finalize msg/Pms5003 message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
void
sniff_msgs__msg__Pms5003__fini(sniff_msgs__msg__Pms5003 * msg);

/// Create msg/Pms5003 message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * sniff_msgs__msg__Pms5003__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
sniff_msgs__msg__Pms5003 *
sniff_msgs__msg__Pms5003__create();

/// Destroy msg/Pms5003 message.
/**
 * It calls
 * sniff_msgs__msg__Pms5003__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
void
sniff_msgs__msg__Pms5003__destroy(sniff_msgs__msg__Pms5003 * msg);

/// Check for msg/Pms5003 message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
bool
sniff_msgs__msg__Pms5003__are_equal(const sniff_msgs__msg__Pms5003 * lhs, const sniff_msgs__msg__Pms5003 * rhs);

/// Copy a msg/Pms5003 message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
bool
sniff_msgs__msg__Pms5003__copy(
  const sniff_msgs__msg__Pms5003 * input,
  sniff_msgs__msg__Pms5003 * output);

/// Initialize array of msg/Pms5003 messages.
/**
 * It allocates the memory for the number of elements and calls
 * sniff_msgs__msg__Pms5003__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
bool
sniff_msgs__msg__Pms5003__Sequence__init(sniff_msgs__msg__Pms5003__Sequence * array, size_t size);

/// Finalize array of msg/Pms5003 messages.
/**
 * It calls
 * sniff_msgs__msg__Pms5003__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
void
sniff_msgs__msg__Pms5003__Sequence__fini(sniff_msgs__msg__Pms5003__Sequence * array);

/// Create array of msg/Pms5003 messages.
/**
 * It allocates the memory for the array and calls
 * sniff_msgs__msg__Pms5003__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
sniff_msgs__msg__Pms5003__Sequence *
sniff_msgs__msg__Pms5003__Sequence__create(size_t size);

/// Destroy array of msg/Pms5003 messages.
/**
 * It calls
 * sniff_msgs__msg__Pms5003__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
void
sniff_msgs__msg__Pms5003__Sequence__destroy(sniff_msgs__msg__Pms5003__Sequence * array);

/// Check for msg/Pms5003 message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
bool
sniff_msgs__msg__Pms5003__Sequence__are_equal(const sniff_msgs__msg__Pms5003__Sequence * lhs, const sniff_msgs__msg__Pms5003__Sequence * rhs);

/// Copy an array of msg/Pms5003 messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_sniff_msgs
bool
sniff_msgs__msg__Pms5003__Sequence__copy(
  const sniff_msgs__msg__Pms5003__Sequence * input,
  sniff_msgs__msg__Pms5003__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // SNIFF_MSGS__MSG__DETAIL__PMS5003__FUNCTIONS_H_
