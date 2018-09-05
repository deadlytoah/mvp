#[derive(Serialize, Deserialize)]
pub enum Level {
    Level1,
    Level2,
    Level3,
    Level4,
    Level5,
}

impl From<u8> for Level {
    fn from(val: u8) -> Level {
        if val > 4 {
            panic!("value {} out of range for Level", val)
        } else {
            unsafe { ::std::mem::transmute(val) }
        }
    }
}
