//! The target-facing semantic boundary.  The current lowering implementation
//! reuses the proven resolver while callers depend only on HIR names.

use std::path::Path;

use crate::compiler::{ParsedProject, ProjectDiagnostic};

pub use crate::semantic::{
    ModuleId, PrimitiveType, ResolvedType as HirType, SemanticAlias as HirAlias,
    SemanticConst as HirConst, SemanticDeclaration as HirDeclaration, SemanticDoc as HirDoc,
    SemanticEnum as HirEnum, SemanticField as HirField, SemanticFunction as HirFunction,
    SemanticImport as HirImport, SemanticModule as HirModule, SemanticNewtype as HirNewtype,
    SemanticParameter as HirParameter, SemanticProject as HirProject, SemanticStruct as HirStruct,
    SemanticValue as HirValue, SemanticVariant as HirVariant, SymbolId,
};

pub fn lower(
    source_root: &Path,
    parsed: ParsedProject,
) -> Result<HirProject, Vec<ProjectDiagnostic>> {
    crate::semantic::analyze_project(source_root, parsed)
}
