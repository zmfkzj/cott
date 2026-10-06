# Rust 컬렉션: 의미 보존 생성 최적화와 측정

## 최종 구현

`Set::new`/`Map::new`는 기존 `PartialEq` API와 선형 구현을 유지한다. `Eq`/`Hash`/`Clone`이나
`'static` bound를 추가하지 않는다. 저장 표현도 기존 Vec-only 그대로여서 lifetime 공변성,
auto-trait와 header 크기를 바꾸지 않는다. Cott의 hash-stable key가 Rust nominal type의
`Hash` 구현을 뜻하는 것은 아니다.

- Set은 동등 원소의 첫 등장 순서를 보존한다.
- Map은 중복 key의 마지막 값과 마지막 등장 위치의 순서를 보존한다.
- `iter`/`into_vec`, 순서와 무관한 equality, `Debug` 표현도 유지한다.
- **조회·동등성은 기존 선형/반복 선형 경로 그대로다. 조회 최적화라고 주장하지 않는다.**

새 `Set::from_scalar`/`Map::from_scalar`는 sealed immutable scalar key만 허용한다.
문자열 입력 64개 이상, 정수 1024개 이상에서 **생성·중복 제거 중에만** 임시 hash index를
사용하고 반환 전에 버린다. bool과 작은 입력은 항상 기존 선형 경로다. compiler는 key가
concrete primitive인 typed literal/default/scenario expression에서 이 constructor를
선택한다. 실제 생성·검증·배포한 crate의 native consumer도 명시적으로 호출할 수 있다.

임시 인덱스는 `RandomState`, std `HashMap<u64,usize>`, collision-chain 위치 Vec다.
동일 hash는 반드시 원래 key equality로 재확인한다. Map은 뒤에서 중복을 제거한 뒤
결과 Vec를 뒤집어 last-occurrence 순서를 보존한다. hash iteration을 외부 순서로
노출하지 않으며, 모든 hash를 같게 만드는 회귀도 통과한다. 외부 custom hash/key를 이
빠른 경로에 넣는 API나 unsafe cast는 없다. 충돌이 길어지면 성능은 다시 나빠질 수 있다.

## 기준선과 후보 선택

시작 미커밋 workspace 전체·hash는 `target/rust-graph-followup/baseline/`와
`baseline-hashes.json`에 보존했다. 이전 Python/진단 작업을 HEAD로 되돌리지 않았다.
변경 전 의미 회귀 2개를 먼저 통과시키고 원래 runtime fragment를
`target/rust-graph-followup/collections-before.rs`에 저장했다.

첫 임계값64 후보는 128개 u64 Set 생성에서 약 1.119→5.199µs로 손해였다. 정수 임계값을
1024로 높이고 bool은 선형 처리했다. 이어 persistent index 후보는 큰 조회를 빠르게 했지만
key 타입을 인자로 받는 저장 함수 포인터가 generic 컬렉션을 invariant로 만들 수 있었다.
기존 borrowed-key 공변성까지 지키기 위해 **그 후보를 채택하지 않고 생성-only 인덱스로
좁혔다**. 이 판단을 regression으로 고정했다. 과거 후보의 source/harness/raw 결과는
작업 소유 `target/rust-graph-followup/persistent-index-*`에 남겼으며 아래 최종 결과와 혼합하지 않는다.

## 최종 microbenchmark

실제 rustc **1.99.0**, edition2024, `-C opt-level=3`, 동일 workload·입력으로 각각 7개 새
프로세스 표본을 수집했다. 크기8/128/2048, u64/String, 입력의 25% 중복, 생성·중복 처리·
전체 key 조회·역순 컬렉션과의 equality를 분리했다. `--cfg indexed`는 constructor를
기존 `new`에서 새 `from_scalar`로 선택할 뿐 최적화 플래그·workload 알고리즘은 같다.
lookup 시간은 단일 get이 아니라 **모든 입력 key를 한 번씩 조회한 batch**다.

| 2048개 생성/중복 제거 중앙값 | before `new` | after `from_scalar` |
|---|---:|---:|
| u64 Set | 201.98µs | 83.94µs |
| u64 Map | 427.29µs | 84.83µs |
| String Set | 3636.71µs | 169.27µs |
| String Map | 5079.66µs | 193.23µs |

String Map 생성 범위는 **5049.00–5127.58µs → 192.70–194.59µs**다. 반면 같은 Map의
조회 batch는 **4671.37→4967.02µs**였다. 조회/equality 코드는 바꾸지 않았지만 메모리 배치·
컴파일·host 변동으로 같거나 느리거나 빨라진 표본이 있으므로 조회 개선을 주장하지 않는다.
128개 u64 Map 생성은 **2.322→2.292µs**, 범위 중첩이다. 작은/낮은 중복 비용 입력까지
일반적인 개선을 보장하지 않는다. 원시 표본·범위는 `results/rust-collections-*.json`에 있다.

측정은 순차 비대응 실험이고 CPU/thermal 상태를 통제하지 않았다. 범위 비중첩은 통계적
유의성 검정이나 앱 처리량 보장이 아니다. microbenchmark는 exact runtime fragment를
직접 컴파일한 것으로 인증된 facade 처리량과 구분한다.

### 메모리

별도 1회 실행의 allocator 호출 수와 **요청한 누적 bytes**를 기록한다. 입력 clone을
포함하고 RSS/live/retained/peak·fragmentation은 측정하지 않는다. allocator counter
자체의 timing overhead도 양쪽 동일하게 포함된다.

2048개 String Map 생성은 **2049→2061회**, 요청 bytes **90,112→241,756**이다.
u64 Map은 **1→13회**, **32,768→151,644 bytes**다. 반환된 컬렉션은 인덱스를 보유하지
않으며 이 x86_64 toolchain에서 Map/Set header는 양쪽 **24바이트**다. 조회/equality는
양쪽 할당 0회다. 생성 중 더 많은 임시 할당으로 중복 검색을 줄이는 trade-off다.

## 실제 compiler-owned 경로의 기능 회귀

`native_indexed_literals_verify_and_public_consumer_keeps_source_compatibility`는 128-key
Map/Set literal scenario를 가진 **독립 authored fixture**를 정상 emit→real verify→deploy한
뒤 실제 Cargo consumer를 offline 빌드·실행한다. 새 constructor와 기존 borrowed-key
`PartialEq` API를 모두 사용한다. 이는 인증 경로의 기능 검증이지 위 microbenchmark의
처리량 수치를 인증하는 절차는 아니다. 기존 generation-first 예제/agent bytes는 건드리지 않았다.

```sh
# 변경 전 정확한 fragment를 작업 소유 위치에 보존한 뒤 같은 하네스로 비교한다.
python3 benchmarks/rust_collections.py --source /path/to/collections-before.rs \
  --rustc /absolute/path/to/rustc --output /tmp/rust-before-new.json
python3 benchmarks/rust_collections.py --source src/rust/runtime/collections.rs \
  --rustc /absolute/path/to/rustc --indexed --output /tmp/rust-after-new.json
COTT_CARGO=/usr/bin/cargo COTT_RUSTC=/usr/bin/rustc \
  cargo test --test rust_collections -- --include-ignored --test-threads=1
cargo fmt --check
cargo test
```

출력은 exclusive-create이므로 새 경로로 재실행한다. 다른 toolchain/하네스/입력을 같은
before/after로 합치지 않는다. 이전 Python·historical 결과는 그대로 보존했다.

## 호환성과 남은 한계

Cott 값/호출 의미, Rust Vec-only 저장 표현, record/wire shape가 같으므로 기존 target별
ABI/schema 번호를 유지했다. 새 additive helper는 compiler/managed/runtime hash가 달라져
정규 emit과 명시적 real verify가 필요하다. 옛 인증을 새 성능/기능의 증거로 쓰지 않고
source hash 수동 갱신·legacy alias/reader·인증 이관을 추가하지 않았다.

이번 새 순수 graph/collection native 검증은 모두 통과했다. 추가로 실행한 기존 Rust
isolated-loopback scenario는 host user namespace 정책 때문에 차단됐다:
`unshare --user --map-root-user --net true`가 `/proc/self/uid_map: Operation not permitted`로
실패했다. 네트워크 sandbox 우회 없이 이 미검증 범위를 유지한다.

`ready_ordered_by`는 `architecture.md` §10.4.1 및 `tests/fixtures/ready_ordered.md`,
전체 검사 영수증은 `results/rust-graph-checks.json`을 참고한다.
