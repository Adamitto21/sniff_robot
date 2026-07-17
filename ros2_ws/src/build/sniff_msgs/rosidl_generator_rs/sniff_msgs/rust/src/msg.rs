#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to sniff_msgs__msg__Pms5003

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Pms5003 {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Pms5003::default())
  }
}

impl rosidl_runtime_rs::Message for Pms5003 {
  type RmwMsg = super::msg::rmw::Pms5003;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        pm1: msg.pm1,
        pm25: msg.pm25,
        pm10: msg.pm10,
        particles_03um: msg.particles_03um,
        particles_05um: msg.particles_05um,
        particles_10um: msg.particles_10um,
        particles_25um: msg.particles_25um,
        sensor_ok: msg.sensor_ok,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      pm1: msg.pm1,
      pm25: msg.pm25,
      pm10: msg.pm10,
      particles_03um: msg.particles_03um,
      particles_05um: msg.particles_05um,
      particles_10um: msg.particles_10um,
      particles_25um: msg.particles_25um,
      sensor_ok: msg.sensor_ok,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      pm1: msg.pm1,
      pm25: msg.pm25,
      pm10: msg.pm10,
      particles_03um: msg.particles_03um,
      particles_05um: msg.particles_05um,
      particles_10um: msg.particles_10um,
      particles_25um: msg.particles_25um,
      sensor_ok: msg.sensor_ok,
    }
  }
}


