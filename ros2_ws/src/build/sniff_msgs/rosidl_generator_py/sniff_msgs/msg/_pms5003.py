# generated from rosidl_generator_py/resource/_idl.py.em
# with input from sniff_msgs:msg/Pms5003.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_Pms5003(type):
    """Metaclass of message 'Pms5003'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('sniff_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'sniff_msgs.msg.Pms5003')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__pms5003
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__pms5003
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__pms5003
            cls._TYPE_SUPPORT = module.type_support_msg__msg__pms5003
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__pms5003

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class Pms5003(metaclass=Metaclass_Pms5003):
    """Message class 'Pms5003'."""

    __slots__ = [
        '_header',
        '_pm1',
        '_pm25',
        '_pm10',
        '_particles_03um',
        '_particles_05um',
        '_particles_10um',
        '_particles_25um',
        '_sensor_ok',
    ]

    _fields_and_field_types = {
        'header': 'std_msgs/Header',
        'pm1': 'float',
        'pm25': 'float',
        'pm10': 'float',
        'particles_03um': 'uint16',
        'particles_05um': 'uint16',
        'particles_10um': 'uint16',
        'particles_25um': 'uint16',
        'sensor_ok': 'boolean',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())
        self.pm1 = kwargs.get('pm1', float())
        self.pm25 = kwargs.get('pm25', float())
        self.pm10 = kwargs.get('pm10', float())
        self.particles_03um = kwargs.get('particles_03um', int())
        self.particles_05um = kwargs.get('particles_05um', int())
        self.particles_10um = kwargs.get('particles_10um', int())
        self.particles_25um = kwargs.get('particles_25um', int())
        self.sensor_ok = kwargs.get('sensor_ok', bool())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.header != other.header:
            return False
        if self.pm1 != other.pm1:
            return False
        if self.pm25 != other.pm25:
            return False
        if self.pm10 != other.pm10:
            return False
        if self.particles_03um != other.particles_03um:
            return False
        if self.particles_05um != other.particles_05um:
            return False
        if self.particles_10um != other.particles_10um:
            return False
        if self.particles_25um != other.particles_25um:
            return False
        if self.sensor_ok != other.sensor_ok:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if __debug__:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value

    @builtins.property
    def pm1(self):
        """Message field 'pm1'."""
        return self._pm1

    @pm1.setter
    def pm1(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'pm1' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'pm1' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._pm1 = value

    @builtins.property
    def pm25(self):
        """Message field 'pm25'."""
        return self._pm25

    @pm25.setter
    def pm25(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'pm25' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'pm25' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._pm25 = value

    @builtins.property
    def pm10(self):
        """Message field 'pm10'."""
        return self._pm10

    @pm10.setter
    def pm10(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'pm10' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'pm10' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._pm10 = value

    @builtins.property
    def particles_03um(self):
        """Message field 'particles_03um'."""
        return self._particles_03um

    @particles_03um.setter
    def particles_03um(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'particles_03um' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'particles_03um' field must be an unsigned integer in [0, 65535]"
        self._particles_03um = value

    @builtins.property
    def particles_05um(self):
        """Message field 'particles_05um'."""
        return self._particles_05um

    @particles_05um.setter
    def particles_05um(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'particles_05um' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'particles_05um' field must be an unsigned integer in [0, 65535]"
        self._particles_05um = value

    @builtins.property
    def particles_10um(self):
        """Message field 'particles_10um'."""
        return self._particles_10um

    @particles_10um.setter
    def particles_10um(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'particles_10um' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'particles_10um' field must be an unsigned integer in [0, 65535]"
        self._particles_10um = value

    @builtins.property
    def particles_25um(self):
        """Message field 'particles_25um'."""
        return self._particles_25um

    @particles_25um.setter
    def particles_25um(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'particles_25um' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'particles_25um' field must be an unsigned integer in [0, 65535]"
        self._particles_25um = value

    @builtins.property
    def sensor_ok(self):
        """Message field 'sensor_ok'."""
        return self._sensor_ok

    @sensor_ok.setter
    def sensor_ok(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'sensor_ok' field must be of type 'bool'"
        self._sensor_ok = value
