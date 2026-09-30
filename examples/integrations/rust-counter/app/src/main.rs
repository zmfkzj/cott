use std::panic::{UnwindSafe, catch_unwind};

use rust_counter::modules::example::counter::{decrement, increment};

fn rejected_boundary(label: &str, operation: impl FnOnce() -> i32 + UnwindSafe) {
    match catch_unwind(operation) {
        Ok(value) => panic!("{label} unexpectedly returned {value}"),
        Err(payload) => {
            assert!(
                payload.is::<rust_counter::cott_runtime::ContractViolation>(),
                "{label} panicked with an unexpected payload"
            );
            println!("{label}: rejected by the contract");
        }
    }
}

fn main() {
    let initial = 0;
    let increased = increment(initial);
    let restored = decrement(increased);
    assert_eq!((initial, increased, restored), (0, 1, 0));
    println!("counter: {initial} -> {increased} -> {restored}");

    let upper = increment(99);
    assert_eq!(upper, 100);
    let below_upper = decrement(upper);
    assert_eq!(below_upper, 99);
    println!("upper endpoint: increment(99) -> {upper}, decrement({upper}) -> {below_upper}");
    rejected_boundary("increment(100)", || increment(100));
    rejected_boundary("decrement(0)", || decrement(0));
}
