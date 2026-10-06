/// Full unique-node permutation + dependency readiness + Unicode scalar minimum tie-break.
/// Rust UTF-8 `str` lexicographic order agrees with scalar order on valid Cott Str.
/// No recursion; borrowed names/edges only, O(V+E) storage and O((V+E) log V) work.
pub fn ready_ordered_by<'a, T: 'a, I: IntoIterator<Item = &'a str>>(
    order: &[String],
    values: &'a [T],
    key: impl Fn(&'a T) -> &'a str,
    dependencies: impl Fn(&'a T) -> I,
) -> bool {
    use std::collections::{BTreeMap, BTreeSet};
    let mut nodes = BTreeMap::new();
    for value in values {
        if nodes.insert(key(value), value).is_some() {
            return false;
        }
    }
    if order.len() != nodes.len() {
        return false;
    }
    let mut incoming = nodes
        .keys()
        .map(|&name| (name, 0usize))
        .collect::<BTreeMap<_, _>>();
    let mut dependents = nodes
        .keys()
        .map(|&name| (name, BTreeSet::new()))
        .collect::<BTreeMap<_, _>>();
    for (&name, &value) in &nodes {
        for dependency in dependencies(value) {
            let Some(targets) = dependents.get_mut(dependency) else {
                return false;
            };
            if targets.insert(name) {
                *incoming.get_mut(name).expect("known node") += 1;
            }
        }
    }
    let mut ready = incoming
        .iter()
        .filter_map(|(&name, &n)| (n == 0).then_some(name))
        .collect::<BTreeSet<_>>();
    for name in order {
        if ready.pop_first() != Some(name.as_str()) {
            return false;
        }
        for target in &dependents[name.as_str()] {
            let count = incoming.get_mut(target).expect("known target");
            *count -= 1;
            if *count == 0 {
                ready.insert(target);
            }
        }
    }
    true
}
