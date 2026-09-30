/// Decreases a counter value by one.
///
/// Callers guarantee `0 < current <= 100`, so `current - 1` lies in `0..=99`
/// and cannot overflow.
pub(crate) fn decrement(current: i32) -> i32 {
    current - 1
}
