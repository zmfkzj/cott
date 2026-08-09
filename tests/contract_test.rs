use cott::contract_test::{Classification, ContractTestStrategy};

#[test]
fn strategy_has_fixed_deterministic_limits() {
    let strategy = ContractTestStrategy::new(
        "foo.bar.run",
        b"canonical-ir",
        Classification::Pure,
        vec!["requires:0".to_owned()],
    );
    assert_eq!(strategy.candidate_limit, 64);
    assert_eq!(strategy.container_length_limit, 3);
    assert_eq!(strategy.json_depth_limit, 4);
    let bytes = strategy.bytes().expect("schema-valid strategy");
    assert!(
        String::from_utf8(bytes)
            .expect("UTF-8")
            .contains("\"symbol\":\"foo.bar.run\"")
    );
}
