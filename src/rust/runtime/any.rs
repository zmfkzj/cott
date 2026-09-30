trait AnyPayload: Send + Sync {
    fn as_any(&self) -> &dyn std::any::Any;
    fn validate(&self);
    fn equal(&self, other: &dyn AnyPayload) -> bool;
    fn snapshot(&self) -> Option<AnyValue>;
}
struct Payload<T>(T);
impl<T: Value + Clone + PartialEq + Send + Sync + 'static> AnyPayload for Payload<T> {
    fn as_any(&self) -> &dyn std::any::Any {
        &self.0
    }
    fn validate(&self) {
        self.0.validate()
    }
    fn equal(&self, other: &dyn AnyPayload) -> bool {
        other.as_any().downcast_ref::<T>() == Some(&self.0)
    }
    fn snapshot(&self) -> Option<AnyValue> {
        T::DEEP_SNAPSHOT.then(|| AnyValue(Arc::new(Payload(self.0.__cott_snapshot()))))
    }
}
#[derive(Clone)]
pub struct AnyValue(Arc<dyn AnyPayload>);
impl AnyValue {
    pub fn new<T: Value + Clone + PartialEq + Send + Sync + 'static>(value: T) -> Self {
        value.validate();
        Self(Arc::new(Payload(value)))
    }
    pub fn downcast_ref<T: 'static>(&self) -> Option<&T> {
        self.0.as_any().downcast_ref()
    }
}
impl std::fmt::Debug for AnyValue {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("AnyValue")
    }
}
impl crate::cott_sealed::Sealed for AnyValue {}
impl Value for AnyValue {
    const DEEP_SNAPSHOT: bool = true;
    fn validate(&self) {
        self.0.validate()
    }
    fn __cott_snapshot(&self) -> Self {
        self.0.snapshot().unwrap_or_else(|| self.clone())
    }
}
fn any_integer(value: &dyn std::any::Any) -> Option<i128> {
    macro_rules! integers{($($ty:ty),*)=>{$(if let Some(v)=value.downcast_ref::<$ty>(){return Some(*v as i128)})*};}
    integers!(i8, i16, i32, i64, u8, u16, u32, u64);
    None
}
fn any_float(value: &dyn std::any::Any) -> Option<f64> {
    value
        .downcast_ref::<f64>()
        .copied()
        .or_else(|| value.downcast_ref::<f32>().map(|v| *v as f64))
}
impl PartialEq for AnyValue {
    fn eq(&self, other: &Self) -> bool {
        let a = self.0.as_any();
        let b = other.0.as_any();
        if let (Some(a), Some(b)) = (any_integer(a), any_integer(b)) {
            return a == b;
        }
        if let (Some(a), Some(b)) = (any_float(a), any_float(b)) {
            return a == b;
        }
        if let (Some(a), Some(b)) = (any_integer(a), any_float(b)) {
            return b.fract() == 0.0 && b as i128 == a;
        }
        if let (Some(a), Some(b)) = (any_float(a), any_integer(b)) {
            return a.fract() == 0.0 && a as i128 == b;
        }
        self.0.equal(other.0.as_ref())
    }
}
#[derive(Clone)]
pub struct Opaque<const TAG: u64>(Arc<dyn std::any::Any + Send + Sync>);
impl<const TAG: u64> Opaque<TAG> {
    pub fn new<T: Send + Sync + 'static>(value: T) -> Self {
        Self(Arc::new(value))
    }
    pub fn downcast_ref<T: 'static>(&self) -> Option<&T> {
        self.0.downcast_ref()
    }
}
impl<const TAG: u64> std::fmt::Debug for Opaque<TAG> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Opaque<{TAG}>")
    }
}
impl<const TAG: u64> PartialEq for Opaque<TAG> {
    fn eq(&self, other: &Self) -> bool {
        Arc::ptr_eq(&self.0, &other.0)
    }
}
