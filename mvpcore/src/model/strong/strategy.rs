#[derive(Serialize, Deserialize)]
pub enum Strategy {
    Simple,
    FocusedLearning,
}

impl From<u8> for Strategy {
    fn from(val: u8) -> Strategy {
        if val > 1 {
            panic!("value {} out of range for Strategy", val)
        } else {
            unsafe { ::std::mem::transmute(val) }
        }
    }
}
