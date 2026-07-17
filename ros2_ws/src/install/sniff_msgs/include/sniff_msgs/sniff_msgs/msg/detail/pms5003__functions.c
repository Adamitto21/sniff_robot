// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from sniff_msgs:msg/Pms5003.idl
// generated code does not contain a copyright notice
#include "sniff_msgs/msg/detail/pms5003__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
sniff_msgs__msg__Pms5003__init(sniff_msgs__msg__Pms5003 * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    sniff_msgs__msg__Pms5003__fini(msg);
    return false;
  }
  // pm1
  // pm25
  // pm10
  // particles_03um
  // particles_05um
  // particles_10um
  // particles_25um
  // sensor_ok
  return true;
}

void
sniff_msgs__msg__Pms5003__fini(sniff_msgs__msg__Pms5003 * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // pm1
  // pm25
  // pm10
  // particles_03um
  // particles_05um
  // particles_10um
  // particles_25um
  // sensor_ok
}

bool
sniff_msgs__msg__Pms5003__are_equal(const sniff_msgs__msg__Pms5003 * lhs, const sniff_msgs__msg__Pms5003 * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // pm1
  if (lhs->pm1 != rhs->pm1) {
    return false;
  }
  // pm25
  if (lhs->pm25 != rhs->pm25) {
    return false;
  }
  // pm10
  if (lhs->pm10 != rhs->pm10) {
    return false;
  }
  // particles_03um
  if (lhs->particles_03um != rhs->particles_03um) {
    return false;
  }
  // particles_05um
  if (lhs->particles_05um != rhs->particles_05um) {
    return false;
  }
  // particles_10um
  if (lhs->particles_10um != rhs->particles_10um) {
    return false;
  }
  // particles_25um
  if (lhs->particles_25um != rhs->particles_25um) {
    return false;
  }
  // sensor_ok
  if (lhs->sensor_ok != rhs->sensor_ok) {
    return false;
  }
  return true;
}

bool
sniff_msgs__msg__Pms5003__copy(
  const sniff_msgs__msg__Pms5003 * input,
  sniff_msgs__msg__Pms5003 * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // pm1
  output->pm1 = input->pm1;
  // pm25
  output->pm25 = input->pm25;
  // pm10
  output->pm10 = input->pm10;
  // particles_03um
  output->particles_03um = input->particles_03um;
  // particles_05um
  output->particles_05um = input->particles_05um;
  // particles_10um
  output->particles_10um = input->particles_10um;
  // particles_25um
  output->particles_25um = input->particles_25um;
  // sensor_ok
  output->sensor_ok = input->sensor_ok;
  return true;
}

sniff_msgs__msg__Pms5003 *
sniff_msgs__msg__Pms5003__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sniff_msgs__msg__Pms5003 * msg = (sniff_msgs__msg__Pms5003 *)allocator.allocate(sizeof(sniff_msgs__msg__Pms5003), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(sniff_msgs__msg__Pms5003));
  bool success = sniff_msgs__msg__Pms5003__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
sniff_msgs__msg__Pms5003__destroy(sniff_msgs__msg__Pms5003 * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    sniff_msgs__msg__Pms5003__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
sniff_msgs__msg__Pms5003__Sequence__init(sniff_msgs__msg__Pms5003__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sniff_msgs__msg__Pms5003 * data = NULL;

  if (size) {
    data = (sniff_msgs__msg__Pms5003 *)allocator.zero_allocate(size, sizeof(sniff_msgs__msg__Pms5003), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = sniff_msgs__msg__Pms5003__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        sniff_msgs__msg__Pms5003__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
sniff_msgs__msg__Pms5003__Sequence__fini(sniff_msgs__msg__Pms5003__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      sniff_msgs__msg__Pms5003__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

sniff_msgs__msg__Pms5003__Sequence *
sniff_msgs__msg__Pms5003__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  sniff_msgs__msg__Pms5003__Sequence * array = (sniff_msgs__msg__Pms5003__Sequence *)allocator.allocate(sizeof(sniff_msgs__msg__Pms5003__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = sniff_msgs__msg__Pms5003__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
sniff_msgs__msg__Pms5003__Sequence__destroy(sniff_msgs__msg__Pms5003__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    sniff_msgs__msg__Pms5003__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
sniff_msgs__msg__Pms5003__Sequence__are_equal(const sniff_msgs__msg__Pms5003__Sequence * lhs, const sniff_msgs__msg__Pms5003__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!sniff_msgs__msg__Pms5003__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
sniff_msgs__msg__Pms5003__Sequence__copy(
  const sniff_msgs__msg__Pms5003__Sequence * input,
  sniff_msgs__msg__Pms5003__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(sniff_msgs__msg__Pms5003);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    sniff_msgs__msg__Pms5003 * data =
      (sniff_msgs__msg__Pms5003 *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!sniff_msgs__msg__Pms5003__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          sniff_msgs__msg__Pms5003__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!sniff_msgs__msg__Pms5003__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
