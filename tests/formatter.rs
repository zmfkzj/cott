use cott::formatter::format;
use cott::parser::parse_cst;
use cott::syntax::Cst;

#[test]
fn lossless_formatter_normalizes_newlines_idempotently() {
    let cst = Cst::parse("module demo.core\r\n\r\nfn run() -> I32\r\n").expect("lex");
    let ast = parse_cst(&cst).expect("parse");
    let once = format(&cst, &ast).expect("format");
    let second_cst = Cst::parse(std::str::from_utf8(&once).expect("UTF-8")).expect("lex formatted");
    let twice = format(
        &second_cst,
        &parse_cst(&second_cst).expect("parse formatted"),
    )
    .expect("format formatted");
    assert_eq!(once, twice);
    assert_eq!(once, b"module demo.core\n\nfn run() -> I32\n");
}

fn formatted(source: &str) -> String {
    let cst = Cst::parse(source).expect("lex");
    let ast = parse_cst(&cst).expect("parse");
    String::from_utf8(format(&cst, &ast).expect("format")).expect("UTF-8")
}

#[test]
fn canonicalizes_spacing_indentation_lists_and_comments() {
    let source = "# attached to module\nmodule demo.core # module\n\nuse foo.{B, A,} # use\n\nstruct Card :\n  # attached to field\n  value:I32=1 # field\n\nfn label( ) -> Str:\n  doc \"\"\"\n  # is doc content\n  \"\"\"\n";
    assert_eq!(
        formatted(source),
        "# attached to module\nmodule demo.core  # module\n\nuse foo.{B, A}  # use\n\nstruct Card:\n    # attached to field\n    value: I32 = 1  # field\n\nfn label() -> Str:\n    doc \"\"\"\n    # is doc content\n    \"\"\"\n"
    );
}

#[test]
fn wraps_legal_comma_lists_at_one_hundred_columns() {
    let source = "module demo.core\n\nfn run(first_parameter_with_a_long_name: Result[Option[I64], Option[I64]], second_parameter_with_a_long_name: Result[Option[I64], Option[I64]]) -> Unit\n";
    let output = formatted(source);
    assert!(output.contains(
        "fn run(\n    first_parameter_with_a_long_name: Result[Option[I64], Option[I64]],\n    second_parameter_with_a_long_name: Result[Option[I64], Option[I64]],\n) -> Unit\n"
    ));
    assert_eq!(formatted(&output), output);
}

#[test]
fn formats_rule_declarations_and_clause_actions() {
    let unformatted = "module demo.rules\n\nrule BaseAssignmentRule:\n  doc \"\"\"\n  Base assignment rule.\n  \"\"\"\n  requires line.len > 0\n  ensures Result.Ok(assignment) => assignment.name.len > 0\n  error ParseAssignmentError.MissingEquals\n\nrule StrictAssignmentRule(BaseAssignmentRule):\n  doc \"\"\"\n  Strict assignment rule.\n  \"\"\"\n  override ensures Result.Ok(assignment) => assignment.name.len > 1\n  delete error ParseAssignmentError.MissingEquals\n  ensures Result.Ok(assignment) => assignment.value.len > 0\n  error ParseAssignmentError.EmptyName\n";
    let expected = "module demo.rules\n\nrule BaseAssignmentRule:\n    doc \"\"\"\n    Base assignment rule.\n    \"\"\"\n\n    requires line.len > 0\n\n    ensures Result.Ok(assignment) => assignment.name.len > 0\n\n    error ParseAssignmentError.MissingEquals\n\nrule StrictAssignmentRule(BaseAssignmentRule):\n    doc \"\"\"\n    Strict assignment rule.\n    \"\"\"\n\n    override ensures Result.Ok(assignment) => assignment.name.len > 1\n\n    delete error ParseAssignmentError.MissingEquals\n\n    ensures Result.Ok(assignment) => assignment.value.len > 0\n\n    error ParseAssignmentError.EmptyName\n";
    let output = formatted(unformatted);
    assert_eq!(output, expected);
    assert_eq!(formatted(&output), expected);
}

#[test]
fn formats_annotations_on_declarations() {
    let source = "module demo.annotated\n\n@entity\n@memo(\"User entity definition\")\nstruct User:\n    id: Str\n\n@pure\n@tag(\"lookup\")\nfn find_user(id: Str) -> Option[User]:\n    doc \"\"\"\n    Looks up a {User} by identifier.\n    \"\"\"\n\n    ensures Option.Some(u) => u.id.len > 0\n";
    let output = formatted(source);
    assert_eq!(output, source);
    assert_eq!(formatted(&output), source);
}

#[test]
fn formats_option_nothing_state_default_stably() {
    let output = formatted(
        "module demo.option_state\n\ntrait Holder:\n  fn value(self)->Option[Any]\n\nimpl HolderState for Holder:\n  state:\n    value:Option[Any]=Option.Nothing\n  fn value(self)->Option[Any]:\n    ensures Option.Nothing=>true\n",
    );
    assert!(output.contains(
        "    state:\n        value: Option[Any] = Option.Nothing\n\n    fn value(self) -> Option[Any]:\n        ensures Option.Nothing => true\n"
    ));
    assert_eq!(formatted(&output), output);
}

#[test]
fn formats_stateful_impls_idempotently_with_comments() {
    let source = r#"# module comment
module demo.impls # module

trait Reader:
  fn read(self)->I32

trait Writer:
  fn write(self,value:I32)->Unit

# concrete comment
@entity
impl Counter for Reader+Writer: # impl
  state:
    count:I32=0 # state
  invariant self.count>=0
  init(count:I32):
    # init contract
    requires count>=0
    ensures self.count==count
  fn read(self)->I32:
    ensures old(self.count)==self.count # snapshot
  fn write(self,value:I32)->Unit:
    requires value>=0
    modifies self.count
    ensures old(self.count)<=self.count
"#;
    let expected = r#"# module comment
module demo.impls  # module

trait Reader:
    fn read(self) -> I32

trait Writer:
    fn write(self, value: I32) -> Unit

# concrete comment
@entity
impl Counter for Reader + Writer:  # impl
    state:
        count: I32 = 0  # state

    invariant self.count >= 0

    init(count: I32):
        # init contract
        requires count >= 0

        ensures self.count == count

    fn read(self) -> I32:
        ensures old(self.count) == self.count  # snapshot

    fn write(self, value: I32) -> Unit:
        requires value >= 0

        modifies self.count

        ensures old(self.count) <= self.count
"#;

    let output = formatted(source);
    assert_eq!(output, expected);
    assert!(output.contains("# concrete comment"));
    assert!(output.contains("# init contract"));
    assert!(output.contains("# snapshot"));
    assert_eq!(formatted(&output), output);
}

#[test]
fn formats_v02_const_generics_match_guards_and_trait_defaults() {
    let source = r#"module v02.surface

struct Matrix[T,const N:U32]:
  values:Array[T,N]
  bytes:Buffer[N]

fn fallback(receiver:Reader,value:I32)->I32

trait Reader:
  fn read(self,value:I32)->I32=fallback

fn guarded(value:Option[I32])->Result[I32,Failure]:
  requires value matches Option.Some(input)=>input>0
  ensures result matches Result.Ok(output)=>output>0
  error Failure.Bad with value matches Option.Some(error_value) when error_value==0
"#;
    let expected = r#"module v02.surface

struct Matrix[T, const N: U32]:
    values: Array[T, N]
    bytes: Buffer[N]

fn fallback(receiver: Reader, value: I32) -> I32

trait Reader:
    fn read(self, value: I32) -> I32 = fallback

fn guarded(value: Option[I32]) -> Result[I32, Failure]:
    requires value matches Option.Some(input) => input > 0

    ensures Result.Ok(output) => output > 0

    error Failure.Bad with value matches Option.Some(error_value) when error_value == 0
"#;
    let output = formatted(source);
    assert_eq!(output, expected);
    assert_eq!(formatted(&output), output);
}

#[test]
fn formats_v03_async_associated_types_and_resource_transitions() {
    let source = r#"module v03.surface

trait Stream[T]:
  type Item:Display+Clone
  fn next(self)->T.Item

resource Door:
  initial Open
  state Open
  state Closed
  terminal Closed
  transition Open->Closed

trait Controller:
  type State
  fn close(self)->Controller.State

impl DoorController for Controller:
  type State=I32
  state:
    primary:Door
    backup:Door
    audit:I32
  fn close(self)->I32:
    requires true
    transitions self.primary:Door.Open->Door.Closed,self.backup:Door.Open->Door.Closed
    modifies self.audit
    ensures true

async fn fetch()->I32:
  effects [IO]
"#;
    let expected = r#"module v03.surface

trait Stream[T]:
    type Item: Display + Clone
    fn next(self) -> T.Item

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

trait Controller:
    type State
    fn close(self) -> Controller.State

impl DoorController for Controller:
    type State = I32
    state:
        primary: Door
        backup: Door
        audit: I32

    fn close(self) -> I32:
        requires true

        transitions self.primary: Door.Open -> Door.Closed, self.backup: Door.Open -> Door.Closed

        modifies self.audit

        ensures true

async fn fetch() -> I32:
    effects [IO]
"#;
    let output = formatted(source);
    assert_eq!(output, expected);
    assert_eq!(formatted(&output), expected);
}

#[test]
fn formats_v04_async_trait_impl_methods_and_protocol_types() {
    let source = r#"module v04.surface

async fn fallback(receiver:Reader,value:I32)->I32

trait Reader:
  async fn read(self,value:I32)->I32=fallback

impl BufferedReader for Reader:
  async fn read(self,value:I32)->I32:
    requires true
    ensures true

alias Items=AsyncIterator[I32]
alias Conversation=AsyncGenerator[I32,Unit]
"#;
    let expected = r#"module v04.surface

async fn fallback(receiver: Reader, value: I32) -> I32

trait Reader:
    async fn read(self, value: I32) -> I32 = fallback

impl BufferedReader for Reader:
    async fn read(self, value: I32) -> I32:
        requires true

        ensures true

alias Items = AsyncIterator[I32]

alias Conversation = AsyncGenerator[I32, Unit]
"#;
    let output = formatted(source);
    assert_eq!(output, expected);
    assert_eq!(formatted(&output), output);
}

#[test]
fn formats_v05_inheritance_specialization_variance_and_dyn() {
    let source = r#"module v05.surface

struct Producer[+T]:
  value:T

trait Reader[T] for Display[T]+Clone:
  fn read(self,value:T)->T

struct BufferedReader:
  id:I32

fn fallback(receiver:BufferedReader,value:I32)->I32

trait NumberReader:
  fn read(self,value:I32)->I32

specialize BufferedReader for NumberReader:
  read=v05.surface.fallback

alias DynamicReader=Dyn[NumberReader]
"#;
    let expected = r#"module v05.surface

struct Producer[+T]:
    value: T

trait Reader[T] for Display[T] + Clone:
    fn read(self, value: T) -> T

struct BufferedReader:
    id: I32

fn fallback(receiver: BufferedReader, value: I32) -> I32

trait NumberReader:
    fn read(self, value: I32) -> I32

specialize BufferedReader for NumberReader:
    read = v05.surface.fallback

alias DynamicReader = Dyn[NumberReader]
"#;
    let output = formatted(source);
    assert_eq!(output, expected);
    assert_eq!(formatted(&output), output);
}

#[test]
fn formats_struct_invariants_and_complete_scenario_fixtures_idempotently() {
    let source = r##"module acceptance.surface

struct Location:
  kind:LocationKind
  target:Str
  fragment:Option[Str]=Option.Nothing
  invariant self.kind!=LocationKind.Web or starts_with(self.target,"https://")
  invariant self.fragment matches Option.Some(value)=>not starts_with(value,"#")

scenario workflow for app.run:
  fixtures:
    fs files:
      file "input.txt" text("input")
      file "payload.bin" hex("00ff")
    http service:
      route "/ok"->response(status:200,body:bytes("ok"),encoding:"utf-8")
      route "/next"->redirect(status:302,location:"/ok")
      route "/slow"->delay(ms:25)
      route "/broken"->disconnect()
    clock clock:
      start_ms:10
      tick_ms:2
    failure denied:
      point:file.write
      occurrence:1
      error:permission_denied
  call model=app.open(files.path("input.txt"))
  spawn request=app.fetch(service.url("/ok"))
  tick
  await request as reply
  assert reply=="ok"
  spawn stale=app.fetch(service.url("/slow"))
  cancel stale
  await stale cancelled
"##;
    let expected = r##"module acceptance.surface

struct Location:
    kind: LocationKind
    target: Str
    fragment: Option[Str] = Option.Nothing

    invariant self.kind != LocationKind.Web or starts_with(self.target, "https://")
    invariant self.fragment matches Option.Some(value) => not starts_with(value, "#")

scenario workflow for app.run:
    fixtures:
        fs files:
            file "input.txt" text("input")
            file "payload.bin" hex("00ff")
        http service:
            route "/ok" -> response(status: 200, body: bytes("ok"), encoding: "utf-8")
            route "/next" -> redirect(status: 302, location: "/ok")
            route "/slow" -> delay(ms: 25)
            route "/broken" -> disconnect()
        clock clock:
            start_ms: 10
            tick_ms: 2
        failure denied:
            point: file.write
            occurrence: 1
            error: permission_denied
    call model = app.open(files.path("input.txt"))
    spawn request = app.fetch(service.url("/ok"))
    tick
    await request as reply
    assert reply == "ok"
    spawn stale = app.fetch(service.url("/slow"))
    cancel stale
    await stale cancelled
"##;
    let output = formatted(source);
    assert_eq!(output, expected);
    assert_eq!(formatted(&output), expected);
}
