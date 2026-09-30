// Static autoref selection occurs at each concrete external facade equality site.
// PartialEq-capable host values use host value semantics; opaque non-comparable hosts use identity.
pub(crate) struct ExternalEquality<T>(pub(crate) std::marker::PhantomData<fn()->T>);
impl<T> Copy for ExternalEquality<T>{}
impl<T> Clone for ExternalEquality<T>{fn clone(&self)->Self{*self}}
pub(crate) trait ExternalEqual<T>{fn external_equal(self,left:&Arc<T>,right:&Arc<T>)->bool;}
impl<T:PartialEq> ExternalEqual<T> for &ExternalEquality<T>{fn external_equal(self,left:&Arc<T>,right:&Arc<T>)->bool{**left==**right}}
impl<T> ExternalEqual<T> for ExternalEquality<T>{fn external_equal(self,left:&Arc<T>,right:&Arc<T>)->bool{Arc::ptr_eq(left,right)}}
