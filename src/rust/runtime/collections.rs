// The stored representation stays Vec-only: no extra bounds, variance or auto-trait changes.
// A temporary collision-checked index accelerates known scalar construction only.
mod scalar_key {
    pub trait Sealed {
        const INDEX_THRESHOLD: usize;
    }
    macro_rules! keys { ($($ty:ty),*) => { $(impl Sealed for $ty { const INDEX_THRESHOLD: usize = 1024; })* }; }
    keys!(i8, i16, i32, i64, u8, u16, u32, u64);
    impl Sealed for String {
        const INDEX_THRESHOLD: usize = 64;
    }
    impl Sealed for bool {
        const INDEX_THRESHOLD: usize = usize::MAX;
    }
}
pub trait ScalarKey: scalar_key::Sealed + Eq + std::hash::Hash {}
impl<T: scalar_key::Sealed + Eq + std::hash::Hash> ScalarKey for T {}
const NO_LINK: usize = usize::MAX;
struct ConstructionIndex {
    seed: std::collections::hash_map::RandomState,
    heads: std::collections::HashMap<u64, usize>,
    next: Vec<usize>,
}
impl ConstructionIndex {
    fn new(size: usize) -> Self {
        Self {
            seed: Default::default(),
            heads: Default::default(),
            next: Vec::with_capacity(size),
        }
    }
    fn hash<K: ScalarKey>(&self, key: &K) -> u64 {
        std::hash::BuildHasher::hash_one(&self.seed, key)
    }
    fn find(&self, hash: u64, mut equal: impl FnMut(usize) -> bool) -> bool {
        let mut position = self.heads.get(&hash).copied().unwrap_or(NO_LINK);
        while position != NO_LINK {
            if equal(position) {
                return true;
            }
            position = self.next[position];
        }
        false
    }
    fn push(&mut self, hash: u64) {
        let position = self.next.len();
        self.next
            .push(self.heads.insert(hash, position).unwrap_or(NO_LINK));
    }
}
#[derive(Clone, Debug)]
pub struct Set<T>(Vec<T>);
impl<T: PartialEq> Set<T> {
    pub fn new(mut values: Vec<T>) -> Self {
        let mut write = 0;
        for read in 0..values.len() {
            if !values[..write].contains(&values[read]) {
                if write != read {
                    values.swap(write, read);
                }
                write += 1;
            }
        }
        values.truncate(write);
        Self(values)
    }
    pub fn contains(&self, value: &T) -> bool {
        self.0.contains(value)
    }
    fn construct_indexed(values: Vec<T>, hash: impl Fn(&ConstructionIndex, &T) -> u64) -> Self {
        let mut index = ConstructionIndex::new(values.len());
        let mut unique = Vec::with_capacity(values.len());
        for value in values {
            let hash = hash(&index, &value);
            if !index.find(hash, |i| unique[i] == value) {
                index.push(hash);
                unique.push(value);
            }
        }
        Self(unique)
    }
}
impl<T: ScalarKey> Set<T> {
    /// Fast scalar construction; the temporary index is NOT retained for lookup.
    pub fn from_scalar(values: Vec<T>) -> Self {
        if values.len() < <T as scalar_key::Sealed>::INDEX_THRESHOLD {
            return Self::new(values);
        }
        Self::construct_indexed(values, ConstructionIndex::hash)
    }
}
impl<T> Set<T> {
    pub fn len(&self) -> usize {
        self.0.len()
    }
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
    pub fn iter(&self) -> std::slice::Iter<'_, T> {
        self.0.iter()
    }
    pub fn into_vec(self) -> Vec<T> {
        self.0
    }
    #[allow(dead_code)]
    pub(crate) fn __cott_from_unique(values: Vec<T>) -> Self {
        Self(values)
    }
}
impl<T: PartialEq> PartialEq for Set<T> {
    fn eq(&self, other: &Self) -> bool {
        self.len() == other.len() && self.iter().all(|v| other.contains(v))
    }
}
impl<T: Eq> Eq for Set<T> {}
#[derive(Clone, Debug)]
pub struct Map<K, V>(Vec<(K, V)>);
impl<K: PartialEq, V> Map<K, V> {
    pub fn new(mut values: Vec<(K, V)>) -> Self {
        let mut write = values.len();
        for read in (0..values.len()).rev() {
            if !values[write..]
                .iter()
                .any(|entry| entry.0 == values[read].0)
            {
                write -= 1;
                if write != read {
                    values.swap(write, read);
                }
            }
        }
        values.drain(..write);
        Self(values)
    }
    pub fn get(&self, key: &K) -> Option<&V> {
        self.0.iter().find(|e| &e.0 == key).map(|e| &e.1)
    }
    fn construct_indexed(
        values: Vec<(K, V)>,
        hash: impl Fn(&ConstructionIndex, &K) -> u64,
    ) -> Self {
        let mut index = ConstructionIndex::new(values.len());
        let mut unique = Vec::with_capacity(values.len());
        for (key, value) in values.into_iter().rev() {
            let hash = hash(&index, &key);
            if !index.find(hash, |i| {
                let entry: &(K, V) = &unique[i];
                entry.0 == key
            }) {
                index.push(hash);
                unique.push((key, value));
            }
        }
        unique.reverse();
        Self(unique)
    }
}
impl<K: ScalarKey, V> Map<K, V> {
    /// Fast scalar construction with last-value/last-position semantics, not a new key bound on `new`.
    pub fn from_scalar(values: Vec<(K, V)>) -> Self {
        if values.len() < <K as scalar_key::Sealed>::INDEX_THRESHOLD {
            return Self::new(values);
        }
        Self::construct_indexed(values, ConstructionIndex::hash)
    }
}
impl<K, V> Map<K, V> {
    pub fn len(&self) -> usize {
        self.0.len()
    }
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
    pub fn iter(&self) -> std::slice::Iter<'_, (K, V)> {
        self.0.iter()
    }
    pub fn into_vec(self) -> Vec<(K, V)> {
        self.0
    }
    #[allow(dead_code)]
    pub(crate) fn __cott_from_unique(values: Vec<(K, V)>) -> Self {
        Self(values)
    }
}
impl<K: PartialEq, V: PartialEq> PartialEq for Map<K, V> {
    fn eq(&self, other: &Self) -> bool {
        self.len() == other.len() && self.iter().all(|(k, v)| other.get(k) == Some(v))
    }
}
impl<K: Eq, V: Eq> Eq for Map<K, V> {}
#[cfg(test)]
mod collection_index_tests {
    use super::*;
    #[test]
    fn collisions_are_always_resolved_by_full_equality() {
        let data = (0..256).map(|i| (i % 97, i)).collect::<Vec<_>>();
        let map = Map::construct_indexed(data.clone(), |_, _| 0);
        assert_eq!(map.into_vec(), Map::new(data).into_vec());
        let values = (0..256).map(|i| i % 97).collect::<Vec<_>>();
        let set = Set::construct_indexed(values.clone(), |_, _| 0);
        assert_eq!(set.into_vec(), Set::new(values).into_vec());
    }
    #[test]
    fn thresholds_and_covariance_stay_compatible() {
        assert_eq!(<u64 as scalar_key::Sealed>::INDEX_THRESHOLD, 1024);
        assert_eq!(<String as scalar_key::Sealed>::INDEX_THRESHOLD, 64);
        assert_eq!(<bool as scalar_key::Sealed>::INDEX_THRESHOLD, usize::MAX);
        fn shorten_set<'a>(s: Set<&'static str>, _: &'a str) -> Set<&'a str> {
            s
        }
        fn shorten_map<'a>(
            m: Map<&'static str, &'static str>,
            _: &'a str,
        ) -> Map<&'a str, &'a str> {
            m
        }
        let short = String::from("short");
        assert!(shorten_set(Set::new(vec!["key"]), &short).contains(&"key"));
        assert_eq!(
            shorten_map(Map::new(vec![("key", "value")]), &short).get(&"key"),
            Some(&"value")
        );
        assert_eq!(
            std::mem::size_of::<Set<u64>>(),
            std::mem::size_of::<Vec<u64>>()
        );
        assert_eq!(
            std::mem::size_of::<Map<u64, u64>>(),
            std::mem::size_of::<Vec<(u64, u64)>>()
        );
    }
}
