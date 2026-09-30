// Stable Rust dimension algebra: expressions are types, never generic const expressions.
mod dimension_sealed {
    pub trait Sealed {}
}
pub trait ConstValue:
    dimension_sealed::Sealed + Clone + std::fmt::Debug + Eq + Send + Sync + 'static
{
    fn value() -> u64;
}
pub trait ConstU8Value: ConstValue {}
pub trait ConstU16Value: ConstValue {}
pub trait ConstU32Value: ConstValue {}
pub trait ConstU64Value: ConstValue {}
macro_rules! dimension_literal {
    ($name:ident, $ty:ty, $bound:ident) => {
        #[derive(Clone, Copy, Debug, PartialEq, Eq)]
        pub struct $name<const N: $ty>;
        impl<const N: $ty> dimension_sealed::Sealed for $name<N> {}
        impl<const N: $ty> ConstValue for $name<N> {
            #[inline]
            fn value() -> u64 {
                N as u64
            }
        }
        impl<const N: $ty> $bound for $name<N> {}
    };
}
dimension_literal!(ConstU8, u8, ConstU8Value);
dimension_literal!(ConstU16, u16, ConstU16Value);
dimension_literal!(ConstU32, u32, ConstU32Value);
dimension_literal!(ConstU64, u64, ConstU64Value);

fn dimension_result(value: Option<u64>, bits: u32) -> u64 {
    let value = value
        .unwrap_or_else(|| violation("const", "validation", "undefined Cott const arithmetic"));
    if !matches!(bits, 8 | 16 | 32 | 64) {
        violation("const", "validation", "invalid Cott const width");
    }
    if bits != 64 && value >= (1u64 << bits) {
        violation(
            "const",
            "validation",
            "Cott const arithmetic exceeds its width",
        );
    }
    value
}
macro_rules! dimension_binary {
    ($name:ident, $operation:ident) => {
        #[derive(Clone, Copy, Debug, PartialEq, Eq)]
        pub struct $name<L: ConstValue, R: ConstValue, const BITS: u32>(
            std::marker::PhantomData<(L, R)>,
        );
        impl<L: ConstValue, R: ConstValue, const BITS: u32> dimension_sealed::Sealed
            for $name<L, R, BITS>
        {
        }
        impl<L: ConstValue, R: ConstValue, const BITS: u32> ConstValue for $name<L, R, BITS> {
            #[inline]
            fn value() -> u64 {
                dimension_result(L::value().$operation(R::value()), BITS)
            }
        }
        impl<L: ConstValue, R: ConstValue> ConstU8Value for $name<L, R, 8> {}
        impl<L: ConstValue, R: ConstValue> ConstU16Value for $name<L, R, 16> {}
        impl<L: ConstValue, R: ConstValue> ConstU32Value for $name<L, R, 32> {}
        impl<L: ConstValue, R: ConstValue> ConstU64Value for $name<L, R, 64> {}
    };
}
dimension_binary!(Add, checked_add);
dimension_binary!(Subtract, checked_sub);
dimension_binary!(Multiply, checked_mul);
dimension_binary!(Divide, checked_div);
dimension_binary!(Remainder, checked_rem);

/// An immutable fixed-length value with a native dimension in its Rust type.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Array<T, D: ConstValue> {
    values: Vec<T>,
    dimension: std::marker::PhantomData<D>,
}
impl<T, D: ConstValue> Array<T, D> {
    pub fn new(values: Vec<T>) -> Self
    where
        T: Value + Clone,
    {
        if u64::try_from(values.len()).ok() != Some(D::value()) {
            violation(
                "Array",
                "validation",
                "length differs from canonical const dimension",
            );
        }
        if T::NEEDS_VALIDATION {
            values.validate();
        }
        Self {
            values,
            dimension: std::marker::PhantomData,
        }
    }
    pub fn len(&self) -> usize {
        self.values.len()
    }
    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }
    pub fn as_slice(&self) -> &[T] {
        &self.values
    }
    pub fn iter(&self) -> std::slice::Iter<'_, T> {
        self.values.iter()
    }
    pub fn into_vec(self) -> Vec<T> {
        self.values
    }
    pub fn map<U: Value + Clone>(self, f: impl FnMut(T) -> U) -> Array<U, D> {
        // Mapping preserves extent; do not reevaluate the canonical dimension.
        let values: Vec<U> = self.values.into_iter().map(f).collect();
        if U::NEEDS_VALIDATION {
            values.validate();
        }
        Array {
            values,
            dimension: std::marker::PhantomData,
        }
    }
}
impl<T, D: ConstValue> std::ops::Deref for Array<T, D> {
    type Target = [T];
    fn deref(&self) -> &[T] {
        self.as_slice()
    }
}
impl<T: Value + Clone, D: ConstValue> crate::cott_sealed::Sealed for Array<T, D> {}
impl<T: Value + Clone, D: ConstValue> Value for Array<T, D> {
    const NEEDS_VALIDATION: bool = T::NEEDS_VALIDATION;
    const DEEP_SNAPSHOT: bool = T::DEEP_SNAPSHOT;
    fn validate(&self) {
        if T::NEEDS_VALIDATION {
            self.values.validate();
        }
    }
    fn __cott_snapshot(&self) -> Self {
        Self {
            values: self.values.__cott_snapshot(),
            dimension: std::marker::PhantomData,
        }
    }
}
impl<T: Value + Clone, D: ConstValue> ConstructionArguments for Array<T, D> {
    type Arguments = Vec<T>;
}
impl<T: Value + Clone, D: ConstValue> Constructible for Array<T, D> {
    fn construct(values: Vec<T>) -> Self {
        Self::new(values)
    }
}
pub type Buffer<D> = Array<u8, D>;
