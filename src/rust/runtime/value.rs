/// Statically typed canonical value validation. No type-parameter erasure or runtime witnesses.
pub trait Value: crate::cott_sealed::Sealed {
    const NEEDS_VALIDATION: bool = true;
    const DEEP_SNAPSHOT: bool = false;
    fn validate(&self);
    fn __cott_snapshot(&self) -> Self
    where
        Self: Sized + Clone,
    {
        self.clone()
    }
}
pub trait ConstructionArguments {
    type Arguments;
}
pub trait Constructible: ConstructionArguments + Value {
    fn construct(arguments: Self::Arguments) -> Self;
}
macro_rules! plain_values{($($ty:ty),* $(,)?)=>{$(impl crate::cott_sealed::Sealed for $ty{}impl Value for $ty{const NEEDS_VALIDATION:bool=false;#[inline]fn validate(&self){}}impl ConstructionArguments for $ty{type Arguments=Self;}impl Constructible for $ty{fn construct(value:Self)->Self{value}})*};}
plain_values!(
    bool,
    i8,
    i16,
    i32,
    i64,
    u8,
    u16,
    u32,
    u64,
    (),
    String,
    Never
);
impl crate::cott_sealed::Sealed for std::path::PathBuf {}
impl Value for std::path::PathBuf {
    fn validate(&self) {
        let path = self
            .to_str()
            .unwrap_or_else(|| violation("path", "validation", "non-UTF-8 path"));
        if path.contains('\0') {
            violation("path", "validation", "NUL in path")
        }
    }
}
impl ConstructionArguments for std::path::PathBuf {
    type Arguments = Self;
}
impl Constructible for std::path::PathBuf {
    fn construct(value: Self) -> Self {
        value.validate();
        value
    }
}
impl crate::cott_sealed::Sealed for f32 {}
impl crate::cott_sealed::Sealed for f64 {}
impl Value for f32 {
    fn validate(&self) {
        finite_f32(*self);
    }
}
impl Value for f64 {
    fn validate(&self) {
        finite_f64(*self);
    }
}
impl ConstructionArguments for f32 {
    type Arguments = Self;
}
impl ConstructionArguments for f64 {
    type Arguments = Self;
}
impl Constructible for f32 {
    fn construct(value: Self) -> Self {
        finite_f32(value)
    }
}
impl Constructible for f64 {
    fn construct(value: Self) -> Self {
        finite_f64(value)
    }
}
pub fn finite_f32(value: f32) -> f32 {
    if !value.is_finite() {
        violation("value", "validation", "non-finite f32")
    }
    value
}
pub fn finite_f64(value: f64) -> f64 {
    if !value.is_finite() {
        violation("value", "validation", "non-finite f64")
    }
    value
}
impl<T: Value + Clone> crate::cott_sealed::Sealed for Vec<T> {}
impl<T: Value + Clone> Value for Vec<T> {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT: bool = T::DEEP_SNAPSHOT;
    fn validate(&self) {
        if T::NEEDS_VALIDATION {
            for value in self {
                value.validate()
            }
        }
    }
    fn __cott_snapshot(&self) -> Self {
        if T::DEEP_SNAPSHOT {
            self.iter().map(Value::__cott_snapshot).collect()
        } else {
            self.clone()
        }
    }
}
impl<T: Value + Clone, const N: usize> crate::cott_sealed::Sealed for [T; N] {}
impl<T: Value + Clone, const N: usize> Value for [T; N] {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT: bool = T::DEEP_SNAPSHOT;
    fn validate(&self) {
        if T::NEEDS_VALIDATION {
            for value in self {
                value.validate()
            }
        }
    }
    fn __cott_snapshot(&self) -> Self {
        if T::DEEP_SNAPSHOT {
            std::array::from_fn(|i| self[i].__cott_snapshot())
        } else {
            self.clone()
        }
    }
}
impl<T: Value + Clone> crate::cott_sealed::Sealed for Option<T> {}
impl<T: Value + Clone> Value for Option<T> {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT: bool = T::DEEP_SNAPSHOT;
    fn validate(&self) {
        if T::NEEDS_VALIDATION {
            if let Some(value) = self {
                value.validate()
            }
        }
    }
    fn __cott_snapshot(&self) -> Self {
        self.as_ref().map(Value::__cott_snapshot)
    }
}
impl<T: Value + Clone, E: Value + Clone> crate::cott_sealed::Sealed for Result<T, E> {}
impl<T: Value + Clone, E: Value + Clone> Value for Result<T, E> {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION || E::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT: bool = T::DEEP_SNAPSHOT || E::DEEP_SNAPSHOT;
    fn validate(&self) {
        if Self::NEEDS_VALIDATION {
            match self {
                Ok(value) => value.validate(),
                Err(error) => error.validate(),
            }
        }
    }
    fn __cott_snapshot(&self) -> Self {
        match self {
            Ok(v) => Ok(v.__cott_snapshot()),
            Err(e) => Err(e.__cott_snapshot()),
        }
    }
}
impl<T:Value+Clone> crate::cott_sealed::Sealed for Box<T>{}
impl<T:Value+Clone> Value for Box<T>{
    const NEEDS_VALIDATION:bool=T::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT:bool=T::DEEP_SNAPSHOT;
    fn validate(&self){if T::NEEDS_VALIDATION{(**self).validate()}}
    fn __cott_snapshot(&self)->Self{Box::new((**self).__cott_snapshot())}
}
impl<T:ConstructionArguments> ConstructionArguments for Box<T>{type Arguments=T::Arguments;}
impl<T:Constructible+Clone> Constructible for Box<T>{fn construct(args:Self::Arguments)->Self{Box::new(T::construct(args))}}
impl<T: Value + ?Sized> crate::cott_sealed::Sealed for Arc<T> {}
impl<T: Value + ?Sized> Value for Arc<T> {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    fn validate(&self) {
        if T::NEEDS_VALIDATION {
            (**self).validate()
        }
    }
}
impl<T: Value + ?Sized> crate::cott_sealed::Sealed for &T {}
impl<T: Value + ?Sized> crate::cott_sealed::Sealed for &mut T {}
impl<T: Value + ?Sized> Value for &T {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    fn validate(&self) {
        (**self).validate()
    }
}
impl<T: Value + ?Sized> Value for &mut T {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    fn validate(&self) {
        (**self).validate()
    }
}
impl<T: Value + Clone> crate::cott_sealed::Sealed for Set<T> {}
impl<T: Value + Clone> Value for Set<T> {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT: bool = T::DEEP_SNAPSHOT;
    fn validate(&self) {
        if T::NEEDS_VALIDATION {
            for value in self.iter() {
                value.validate()
            }
        }
    }
    fn __cott_snapshot(&self) -> Self {
        if T::DEEP_SNAPSHOT {
            Self(self.iter().map(Value::__cott_snapshot).collect())
        } else {
            self.clone()
        }
    }
}
impl<K: Value + Clone, V: Value + Clone> crate::cott_sealed::Sealed for Map<K, V> {}
impl<K: Value + Clone, V: Value + Clone> Value for Map<K, V> {
    const NEEDS_VALIDATION: bool = K::NEEDS_VALIDATION || V::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT: bool = K::DEEP_SNAPSHOT || V::DEEP_SNAPSHOT;
    fn validate(&self) {
        if Self::NEEDS_VALIDATION {
            for (key, value) in self.iter() {
                key.validate();
                value.validate()
            }
        }
    }
    fn __cott_snapshot(&self) -> Self {
        if Self::DEEP_SNAPSHOT {
            Self(
                self.iter()
                    .map(|(k, v)| (k.__cott_snapshot(), v.__cott_snapshot()))
                    .collect(),
            )
        } else {
            self.clone()
        }
    }
}
impl crate::cott_sealed::Sealed for JsonValue {}
impl Value for JsonValue {
    fn validate(&self) {
        match self {
            Self::Number(value) => value.validate(),
            Self::Array(values) => values.validate(),
            Self::Object(values) => {
                for value in values.values() {
                    value.validate()
                }
            }
            _ => {}
        }
    }
}
impl<const TAG: u64> crate::cott_sealed::Sealed for Opaque<TAG> {}
impl<const TAG: u64> Value for Opaque<TAG> {
    const NEEDS_VALIDATION: bool = false;
    fn validate(&self) {}
}
impl<T> crate::cott_sealed::Sealed for IteratorValue<T> {}
impl<T> Value for IteratorValue<T> {
    const NEEDS_VALIDATION: bool = false;
    fn validate(&self) {}
}
impl<T> crate::cott_sealed::Sealed for AsyncIteratorValue<T> {}
impl<T> Value for AsyncIteratorValue<T> {
    const NEEDS_VALIDATION: bool = false;
    fn validate(&self) {}
}
impl<Y, S, R> crate::cott_sealed::Sealed for Generator<Y, S, R> {}
impl<Y, S, R> Value for Generator<Y, S, R> {
    const NEEDS_VALIDATION: bool = false;
    fn validate(&self) {}
}
impl<Y, S> crate::cott_sealed::Sealed for AsyncGenerator<Y, S> {}
impl<Y, S> Value for AsyncGenerator<Y, S> {
    const NEEDS_VALIDATION: bool = false;
    fn validate(&self) {}
}
impl<T: ConstructionArguments> crate::cott_sealed::Sealed for Factory<T> {}
impl<T: ConstructionArguments> Value for Factory<T> {
    const NEEDS_VALIDATION: bool = false;
    fn validate(&self) {}
}
impl<T: ?Sized> crate::cott_sealed::Sealed for Dyn<T> {}
impl<T: ?Sized> Value for Dyn<T> {
    const NEEDS_VALIDATION: bool = false;
    fn validate(&self) {}
}
macro_rules! tuple_values{($($type:ident:$index:tt),+)=>{impl<$($type:Value+Clone),+> crate::cott_sealed::Sealed for ($($type,)+){}impl<$($type:Value+Clone),+> Value for ($($type,)+){const NEEDS_VALIDATION:bool=false$(||$type::NEEDS_VALIDATION)+;const DEEP_SNAPSHOT:bool=false$(||$type::DEEP_SNAPSHOT)+;fn validate(&self){$(if $type::NEEDS_VALIDATION{self.$index.validate();})+}fn __cott_snapshot(&self)->Self{($(self.$index.__cott_snapshot(),)+)}}};}
tuple_values!(A:0);
tuple_values!(A:0,B:1);
tuple_values!(A:0,B:1,C:2);
tuple_values!(A:0,B:1,C:2,D:3);
tuple_values!(A:0,B:1,C:2,D:3,E:4);
tuple_values!(A:0,B:1,C:2,D:3,E:4,F:5);
tuple_values!(A:0,B:1,C:2,D:3,E:4,F:5,G:6);
tuple_values!(A:0,B:1,C:2,D:3,E:4,F:5,G:6,H:7);
tuple_values!(A:0,B:1,C:2,D:3,E:4,F:5,G:6,H:7,I:8);
tuple_values!(A:0,B:1,C:2,D:3,E:4,F:5,G:6,H:7,I:8,J:9);
tuple_values!(A:0,B:1,C:2,D:3,E:4,F:5,G:6,H:7,I:8,J:9,K:10);
tuple_values!(A:0,B:1,C:2,D:3,E:4,F:5,G:6,H:7,I:8,J:9,K:10,L:11);

#[doc(hidden)]
pub struct Fixture {
    root: std::path::PathBuf,
    base_url: String,
    allowed: std::collections::BTreeSet<String>,
}
#[doc(hidden)]
pub fn __cott_fixture(
    root: std::path::PathBuf,
    base_url: String,
    allowed: std::collections::BTreeSet<String>,
) -> Fixture {
    Fixture {
        root,
        base_url,
        allowed,
    }
}
#[doc(hidden)]
pub fn __cott_fixture_path(fixture: &Fixture, path: &str) -> std::path::PathBuf {
    if !fixture.allowed.contains(path)
        || std::path::Path::new(path)
            .components()
            .any(|c| !matches!(c, std::path::Component::Normal(_)))
    {
        violation("fixture", "validation", "path outside finite fixture")
    }
    fixture.root.join(path)
}
#[doc(hidden)]
pub fn __cott_fixture_url(fixture: &Fixture, path: &str) -> String {
    if !fixture.allowed.contains(path) {
        violation("fixture", "validation", "URL outside finite fixture")
    }
    format!("{}{}", fixture.base_url, path)
}
