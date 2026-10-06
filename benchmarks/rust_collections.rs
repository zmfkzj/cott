// Standalone microbenchmark of the exact compiler runtime fragment, not certified facade evidence.
mod runtime {
    include!(env!("COTT_COLLECTION_SOURCE"));
}
use runtime::{Map, Set};
use std::{
    hint::black_box,
    sync::atomic::{AtomicUsize, Ordering},
    time::Instant,
};
struct Counted;
static CALLS: AtomicUsize = AtomicUsize::new(0);
static BYTES: AtomicUsize = AtomicUsize::new(0);
unsafe impl std::alloc::GlobalAlloc for Counted {
    unsafe fn alloc(&self, l: std::alloc::Layout) -> *mut u8 {
        CALLS.fetch_add(1, Ordering::Relaxed);
        BYTES.fetch_add(l.size(), Ordering::Relaxed);
        unsafe { std::alloc::System.alloc(l) }
    }
    unsafe fn dealloc(&self, p: *mut u8, l: std::alloc::Layout) {
        unsafe { std::alloc::System.dealloc(p, l) }
    }
    unsafe fn realloc(&self, p: *mut u8, l: std::alloc::Layout, n: usize) -> *mut u8 {
        CALLS.fetch_add(1, Ordering::Relaxed);
        BYTES.fetch_add(n, Ordering::Relaxed);
        unsafe { std::alloc::System.realloc(p, l, n) }
    }
}
#[global_allocator]
static ALLOCATOR: Counted = Counted;
fn sample(mut call: impl FnMut(), loops: usize) -> (u128, usize, usize) {
    for _ in 0..3 {
        call();
    }
    let start = Instant::now();
    for _ in 0..loops {
        call();
    }
    let elapsed = start.elapsed().as_nanos() / loops as u128;
    CALLS.store(0, Ordering::Relaxed);
    BYTES.store(0, Ordering::Relaxed);
    call();
    (
        elapsed,
        CALLS.load(Ordering::Relaxed),
        BYTES.load(Ordering::Relaxed),
    )
}
fn exercise<K: Clone + PartialEq + std::fmt::Debug>(
    kind: &str,
    n: usize,
    keys: Vec<K>,
    set_new: fn(Vec<K>) -> Set<K>,
    map_new: fn(Vec<(K, usize)>) -> Map<K, usize>,
) {
    let loops = if n > 1000 { 20 } else { 200 };
    let set = set_new(keys.clone());
    let map = map_new(
        keys.iter()
            .cloned()
            .enumerate()
            .map(|(i, k)| (k, i))
            .collect(),
    );
    let reverse = set_new(keys.iter().rev().cloned().collect());
    let reverse_map = map_new(map.iter().rev().cloned().collect());
    assert_eq!(set, reverse);
    assert_eq!(map, reverse_map);
    for op in [
        "set_create",
        "map_create",
        "set_lookup",
        "map_lookup",
        "set_equal",
        "map_equal",
    ] {
        let (ns, allocs, bytes) = sample(
            || match op {
                "set_create" => {
                    black_box(set_new(black_box(keys.clone())));
                }
                "map_create" => {
                    black_box(map_new(black_box(
                        keys.iter()
                            .cloned()
                            .enumerate()
                            .map(|(i, k)| (k, i))
                            .collect(),
                    )));
                }
                "set_lookup" => {
                    for k in &keys {
                        assert!(black_box(&set).contains(black_box(k)));
                    }
                }
                "map_lookup" => {
                    for k in &keys {
                        assert!(black_box(&map).get(black_box(k)).is_some());
                    }
                }
                "set_equal" => {
                    assert!(black_box(&set) == black_box(&reverse));
                }
                _ => {
                    assert!(black_box(&map) == black_box(&reverse_map));
                }
            },
            loops,
        );
        println!("{kind},{n},{op},{ns},{allocs},{bytes}");
    }
}
fn main() {
    eprintln!(
        "set_u64_size={} map_u64_size={}",
        std::mem::size_of::<Set<u64>>(),
        std::mem::size_of::<Map<u64, u64>>()
    );
    for n in [8, 128, 2048] {
        // 25% duplicated entries. Same input/algorithm on both sides.
        let ints = (0..n).map(|i| (i % (n * 3 / 4)) as u64).collect::<Vec<_>>();
        let strings = ints
            .iter()
            .map(|i| format!("key-{i:08}"))
            .collect::<Vec<_>>();
        #[cfg(not(indexed))]
        {
            exercise("u64", n, ints, Set::new, Map::new);
            exercise("str", n, strings, Set::new, Map::new);
        }
        #[cfg(indexed)]
        {
            exercise("u64", n, ints, Set::from_scalar, Map::from_scalar);
            exercise("str", n, strings, Set::from_scalar, Map::from_scalar);
        }
    }
}
