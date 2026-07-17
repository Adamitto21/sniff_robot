#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "sniff_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__sniff_msgs__msg__Pms5003() -> *const std::ffi::c_void;
}

#[link(name = "sniff_msgs__rosidl_generator_c")]
extern "C" {
    fn sniff_msgs__msg__Pms5003__init(msg: *mut Pms5003) -> bool;
    fn sniff_msgs__msg__Pms5003__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Pms5003>, size: usize) -> bool;
    fn sniff_msgs__msg__Pms5003__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Pms5003>);
    fn sniff_msgs__msg__Pms5003__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Pms5003>, out_seq: *mut rosidl_runtime_rs::Sequence<Pms5003>) -> bool;
}

// Corresponds to sniff_msgs__msg__Pms5003
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Pms5003 {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pm1: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pm25: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pm10: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub particles_03um: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub particles_05um: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub particles_10um: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub particles_25um: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub sensor_ok: bool,

}



impl Default for Pms5003 {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !sniff_msgs__msg__Pms5003__init(&mut msg as *mut _) {
        panic!("Call to sniff_msgs__msg__Pms5003__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Pms5003 {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sniff_msgs__msg__Pms5003__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sniff_msgs__msg__Pms5003__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { sniff_msgs__msg__Pms5003__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Pms5003 {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Pms5003 where Self: Sized {
  const TYPE_NAME: &'static str = "sniff_msgs/msg/Pms5003";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__sniff_msgs__msg__Pms5003() }
  }
}


