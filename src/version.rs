pub fn parse_version(value: &str) -> Option<(u64, u64, u64)> {
    let mut parts = value
        .split_whitespace()
        .next()?
        .split('.')
        .map(str::parse::<u64>);
    let (Some(Ok(major)), Some(Ok(minor)), Some(Ok(patch))) =
        (parts.next(), parts.next(), parts.next())
    else {
        return None;
    };
    parts.next().is_none().then_some((major, minor, patch))
}

pub fn is_at_least(value: &str, minimum: (u64, u64, u64)) -> bool {
    parse_version(value).is_some_and(|version| version >= minimum)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_numeric_version_tokens_at_or_above_the_minimum() {
        assert!(is_at_least("0.12.3", (0, 12, 3)));
        assert!(is_at_least("1.0.0", (0, 12, 3)));
        assert!(is_at_least("0.12.5 (x86_64-unknown-linux-gnu)", (0, 12, 3)));
        assert!(!is_at_least("0.12.2", (0, 12, 3)));
        assert!(!is_at_least("0.12", (0, 12, 3)));
        assert!(!is_at_least("0.12.3-dev", (0, 12, 3)));
    }
}
