//! Python target boundary. Existing emit/runtime implementation is exposed
//! through this module while target APIs migrate to Canonical IR inputs.

pub use crate::binding;
pub mod artifact_plan;
pub use crate::python_emit as emit;
pub use crate::python_runtime as runtime;
