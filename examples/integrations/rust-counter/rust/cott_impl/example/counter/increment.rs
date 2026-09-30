/// Increases a counter value by one.
///
/// The contract requires `0 <= current < 100`, so `current + 1` lies in
/// `1..=100` and cannot overflow `i32`; the result equals `current + 1`.
pub(crate) fn increment(current: i32) -> i32 {
    current + 1
}
