#[allow(dead_code)]
mod runtime {
    include!("../src/rust/runtime/collections.rs");
}
use runtime::{Map, Set};

#[test]
fn public_partial_eq_api_preserves_order_duplicates_and_equality() {
    let set = Set::new(vec![3, 1, 3, 2, 1]);
    assert_eq!(set.iter().copied().collect::<Vec<_>>(), [3, 1, 2]);
    assert_eq!(set, Set::new(vec![2, 1, 3]));
    assert_eq!(set.into_vec(), [3, 1, 2]);
    let map = Map::new(vec![
        (1, "old"),
        (2, "two"),
        (1, "new"),
        (3, "three"),
        (2, "last"),
    ]);
    assert_eq!(
        map.iter().cloned().collect::<Vec<_>>(),
        [(1, "new"), (3, "three"), (2, "last")]
    );
    assert_eq!(map, Map::new(vec![(2, "last"), (1, "new"), (3, "three")]));
    assert_eq!(map.get(&1), Some(&"new"));
    assert_eq!(map.get(&4), None);
    assert_eq!(map.into_vec(), [(1, "new"), (3, "three"), (2, "last")]);
    assert!(Set::<String>::new(vec![]).is_empty());
    assert!(Map::<String, i32>::new(vec![]).is_empty());
}

#[test]
fn source_compatibility_keeps_borrowed_partial_eq_only_keys() {
    #[derive(Debug, PartialEq)]
    struct Borrowed<'a>(&'a str); // deliberately no Clone/Eq/Hash/'static
    let text = String::from("borrowed");
    let set = Set::new(vec![Borrowed(&text), Borrowed(&text)]);
    assert_eq!(set.len(), 1);
    assert!(set.contains(&Borrowed(&text)));
    let map = Map::new(vec![(Borrowed(&text), 1), (Borrowed(&text), 2)]);
    assert_eq!(map.get(&Borrowed(&text)), Some(&2));
    assert_eq!(Set::new(vec![f64::NAN, f64::NAN]).len(), 2);
}

#[test]
fn indexed_constructors_match_legacy_for_empty_small_large_and_duplicate_keys() {
    for n in [0, 1, 8, 63, 64, 65, 256, 2048] {
        let values = (0..n)
            .map(|i| format!("key-{}", i % 37))
            .collect::<Vec<_>>();
        let set = Set::from_scalar(values.clone());
        let legacy = Set::new(values.clone());
        assert_eq!(set, legacy);
        assert_eq!(legacy, set);
        assert_eq!(set.clone().into_vec(), legacy.into_vec());
        assert_eq!(set.contains(&"absent".to_owned()), false);
        let pairs = values
            .into_iter()
            .enumerate()
            .map(|(i, k)| (k, i))
            .collect::<Vec<_>>();
        let map = Map::from_scalar(pairs.clone());
        let old = Map::new(pairs);
        assert_eq!(map, old);
        assert_eq!(old, map);
        assert_eq!(map.clone().into_vec(), old.into_vec());
        assert_eq!(map.get(&"absent".to_owned()), None);
        for (key, value) in map.iter() {
            assert_eq!(map.get(key), Some(value));
        }
    }
}

#[test]
#[ignore = "requires real absolute COTT_CARGO/COTT_RUSTC, offline dependencies and sandbox"]
fn native_indexed_literals_verify_and_public_consumer_keeps_source_compatibility() {
    use cott::{
        compiler::{SourceFile, parse_project},
        hir::lower,
        ir::render,
    };
    use std::{
        fs,
        path::{Path, PathBuf},
        process::Command,
    };
    let cargo = PathBuf::from(std::env::var_os("COTT_CARGO").expect("COTT_CARGO"));
    let rustc = PathBuf::from(std::env::var_os("COTT_RUSTC").expect("COTT_RUSTC"));
    assert!(cargo.is_absolute() && rustc.is_absolute());
    let root = std::env::temp_dir().join(format!("cott-indexed-native-{}", std::process::id()));
    fs::create_dir(&root).unwrap();
    fs::create_dir(root.join("src")).unwrap();
    fs::create_dir(root.join("rust")).unwrap();
    let keys = (0..128).map(|i| format!("\"key-{i}\"")).collect::<Vec<_>>();
    let pairs = keys
        .iter()
        .enumerate()
        .map(|(i, k)| format!("{k}: {i}"))
        .collect::<Vec<_>>();
    let source = format!(
        "module collections\nfn count(values: Map[Str, U32], keys: Set[Str]) -> U64:\n    ensures result == values.len + keys.len\n\nscenario large:\n    call n = count(Map({}), Set({}))\n    assert n == 256\n",
        pairs.join(", "),
        keys.join(", ")
    );
    fs::write(root.join("src/collections.cott"), &source).unwrap();
    let ir = render(
        &lower(
            Path::new("src"),
            parse_project([SourceFile::new("collections.cott", source)]).unwrap(),
        )
        .unwrap(),
    )
    .unwrap();
    let plan = cott::rust::RustPlan::from_ir(&ir).unwrap();
    let signature =
        cott::rust::emit::implementation_signature(&plan, &plan.callables()[0]).unwrap();
    fs::write(
        root.join("rust/count.rs"),
        format!("{signature} {{ (values.len() + keys.len()) as u64 }}\n"),
    )
    .unwrap();
    fs::write(root.join("cott.toml"),format!("[project]\nname=\"collection_probe\"\nversion=\"0.1.0\"\nsource=\"src\"\n[target.rust]\nsource=\"rust\"\ngenerated=\"generated/rust\"\ncargo={cargo:?}\nrustc={rustc:?}\nruntime_validation=\"boundary\"\n[target.rust.implementations]\n\"collections.count\"=\"count.rs:count\"\n")).unwrap();
    for args in [
        vec!["emit", "rust"],
        vec!["verify"],
        vec!["deploy", "--output", "release"],
    ] {
        let output = Command::new(env!("CARGO_BIN_EXE_cott"))
            .current_dir(&root)
            .args(&args)
            .arg("--project")
            .arg(&root)
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{args:?}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    let record: serde_json::Value =
        serde_json::from_slice(&fs::read(root.join("generated/generation.json")).unwrap()).unwrap();
    assert_eq!(record["current"], record["last_verified"]);
    let app = root.join("consumer");
    fs::create_dir(&app).unwrap();
    fs::create_dir(app.join("src")).unwrap();
    fs::write(app.join("Cargo.toml"),"[package]\nname=\"collections_consumer\"\nversion=\"0.1.0\"\nedition=\"2024\"\n[dependencies]\ncollection_probe={path=\"../release\"}\n").unwrap();
    fs::write(app.join("src/main.rs"),r#"use collection_probe::{cott_runtime::{Map, Set},modules::collections::count};
fn main() {
    let keys=(0..128).map(|i|format!("k-{i}")).collect::<Vec<_>>();
    let map=Map::from_scalar(keys.iter().enumerate().map(|(i,k)|(k.clone(),i as u32)).collect());
    let set=Set::from_scalar(keys.clone());
    assert_eq!(count(map.clone(),set.clone()),256);
    for (i,k) in keys.iter().enumerate(){assert_eq!(map.get(k),Some(&(i as u32)));assert!(set.contains(k));}
    #[derive(PartialEq)] struct Borrowed<'a>(&'a str);
    let local=String::from("borrowed");let old=Map::new(vec![(Borrowed(&local),1),(Borrowed(&local),2)]);assert_eq!(old.get(&Borrowed(&local)),Some(&2));
    let dup=Map::from_scalar(vec![(1u64,1),(2,2),(1,3)]);assert_eq!(dup.into_vec(),vec![(2,2),(1,3)]);
}
"#).unwrap();
    let output = Command::new(&cargo)
        .args(["run", "--offline", "--quiet"])
        .env("RUSTC", &rustc)
        .env_remove("CARGO_TARGET_DIR")
        .current_dir(&app)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    if let Some(out) = std::env::var_os("COTT_READY_EVIDENCE") {
        let out = PathBuf::from(out);
        fs::create_dir_all(&out).unwrap();
        fs::write(
            out.join("collections-verified.json"),
            serde_json::to_vec_pretty(&record).unwrap(),
        )
        .unwrap();
    }
    fs::remove_dir_all(root).unwrap();
}
