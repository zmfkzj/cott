use std::collections::BTreeMap;
use std::path::PathBuf;

const RUNTIME_TEMPLATE: &str = r####"// Cott's compiler-owned, standard-library-only Dart runtime.
// It is portable across the Dart VM and Flutter web.
import 'dart:async';
import 'dart:collection';
import 'dart:core';
import 'dart:core' as core;
import 'dart:convert';
import 'dart:typed_data';

typedef I8 = int;
typedef I16 = int;
typedef I32 = int;
typedef I64 = BigInt;
typedef U8 = int;
typedef U16 = int;
typedef U32 = int;
typedef U64 = BigInt;
typedef F32 = double;
typedef F64 = double;
typedef Result<T, E> = CottResult<T, E>;
typedef Option<T> = CottOption<T>;

const String cottProjectName = __COTT_PROJECT_NAME_LITERAL__;
const String cottProjectVersion = __COTT_PROJECT_VERSION_LITERAL__;
const String cottCompilerVersion = __COTT_RUNTIME_VERSION_LITERAL__;
const int cottRuntimeAbi = 2;

enum RuntimeValidation { boundary, testOnly, off }

enum CottIntKind {
  i8(true, 8, false),
  i16(true, 16, false),
  i32(true, 32, false),
  i64(true, 64, true),
  u8(false, 8, false),
  u16(false, 16, false),
  u32(false, 32, false),
  u64(false, 64, true);

  const CottIntKind(this.signed, this.bits, this.usesBigInt);
  final bool signed;
  final int bits;
  final bool usesBigInt;
}

abstract interface class CottConst {
  BigInt get value;
}

abstract interface class CottOpaqueTag {
  String get tag;
}

enum CottVariance { invariant, covariant, contravariant }

/// Runtime witness for Cott generic arguments. Generated generic nominal
/// values implement this because Dart's covariant type tests are not proof of
/// Cott variance compatibility.
abstract interface class CottGenericValue {
  String get cottGenericIdentity;
  CottList<CottType<Object?>> get cottTypeArguments;
}

abstract interface class CottFieldValue {
  String get cottTypeIdentity;
  CottList<String> get cottFieldNames;
  Object? cottField(String name);
}

/// Compiler-generated private carriers implement this interface. A checked
/// public view never relies on Dart's covariant generic cast; the runtime
/// validates the carrier's explicit Cott witnesses before rebuilding a view.
abstract interface class CottNominalCarrier
    implements CottGenericValue, CottFieldValue {
  CottNominalCarrier cottRebuildCarrier(CottList<Object?> fields);
}
final class CottViewAccess {
  const CottViewAccess._(this._seal);
  final Object _seal;
  bool allows(Object seal) => identical(_seal, seal);
}

abstract interface class CottCheckedView
    implements CottGenericValue, CottFieldValue {
  CottNominalCarrier cottCarrier(CottViewAccess access);
}

abstract interface class CottVariant implements CottFieldValue {
  String get cottVariant;
  CottList<Object?> get cottPayload;
}

abstract interface class CottTupleValue {
  CottList<Object?> get cottTupleElements;
  CottTupleValue cottRebuild(CottList<Object?> elements);
}

abstract interface class CottTraitCarrier {
  CottSet<CottTrait<dynamic>> get cottTraits;
}

final class CottSpan {
  CottSpan({
    required this.startByte,
    required this.endByte,
    required this.startLine,
    required this.startColumn,
    required this.endLine,
    required this.endColumn,
  }) {
    if (startByte < 0 || endByte < startByte) {
      throw ArgumentError('invalid byte span');
    }
    if (startLine < 1 || endLine < startLine) {
      throw ArgumentError('invalid line span');
    }
    if (startColumn < 1 || endColumn < 1) {
      throw ArgumentError('invalid column span');
    }
  }

  final int startByte;
  final int endByte;
  final int startLine;
  final int startColumn;
  final int endLine;
  final int endColumn;

  @override
  bool operator ==(Object other) =>
      other is CottSpan &&
      startByte == other.startByte &&
      endByte == other.endByte &&
      startLine == other.startLine &&
      startColumn == other.startColumn &&
      endLine == other.endLine &&
      endColumn == other.endColumn;

  @override
  int get hashCode => Object.hash(
        startByte,
        endByte,
        startLine,
        startColumn,
        endLine,
        endColumn,
      );
}

class CottContractViolation implements Exception {
  CottContractViolation(
    this.detail, {
    this.symbol,
    this.phase,
    this.span,
    this.expected,
    this.actual,
    this.clause,
    this.cause,
    this.causeStackTrace,
  });

  final String detail;
  String? symbol;
  final String? phase;
  CottSpan? span;
  final String? expected;
  final String? actual;
  final String? clause;
  final Object? cause;
  final StackTrace? causeStackTrace;

  @override
  String toString() {
    final result = StringBuffer('CottContractViolation: $detail');
    for (final entry in <MapEntry<String, Object?>>[
      MapEntry('symbol', symbol),
      MapEntry('phase', phase),
      MapEntry('clause', clause),
      MapEntry('expected', expected),
      MapEntry('actual', actual),
    ]) {
      if (entry.value != null) result.write(' [${entry.key}=${entry.value}]');
    }
    return result.toString();
  }
}

final class CottCancellationException implements Exception {
  const CottCancellationException(this.reason);
  final Object? reason;

  @override
  String toString() => 'CottCancellationException: ${reason ?? 'cancelled'}';
}

enum CottObservationStatus { passed, failed, unobserved }

final class CottClauseObservation {
  const CottClauseObservation({
    required this.symbol,
    required this.clause,
    required this.phase,
    required this.status,
    this.reason,
  });

  final String symbol;
  final String clause;
  final String phase;
  final CottObservationStatus status;
  final String? reason;
  bool? get passed => switch (status) {
        CottObservationStatus.passed => true,
        CottObservationStatus.failed => false,
        CottObservationStatus.unobserved => null,
      };

  Map<String, Object?> toJson() => Map<String, Object?>.unmodifiable({
        'symbol': symbol,
        'clause': clause,
        'phase': phase,
        'status': status.name,
        'reason': reason,
      });
}

final class CottObservation {
  final List<CottClauseObservation> _values = <CottClauseObservation>[];

  void _record(CottClauseObservation observation) => _values.add(observation);

  CottList<CottClauseObservation> observations() => CottList(_values);

  Map<String, Object?> toJson() => Map<String, Object?>.unmodifiable({
        'clauses': List<Map<String, Object?>>.unmodifiable(
          _values.map((value) => value.toJson()),
        ),
      });

  String toJsonString() => jsonEncode(toJson());
}

final class CottUnit {
  const CottUnit._();
  static const CottUnit instance = CottUnit._();
  static const CottUnit value = instance;

  @override
  String toString() => 'UNIT';
}

const CottUnit UNIT = CottUnit.instance;

sealed class CottOption<T> {
  const CottOption();
}

final class Some<T> extends CottOption<T> {
  const Some(this.value);
  final T value;

  @override
  bool operator ==(Object other) =>
      other is Some<Object?> && CottRuntime.deepEqual(value, other.value);

  @override
  int get hashCode => CottRuntime.deepHash(value);

  @override
  String toString() => 'Some($value)';
}

final class Nothing<T> extends CottOption<T> {
  const Nothing();

  @override
  bool operator ==(Object other) => other is Nothing<Object?>;

  @override
  int get hashCode => 0x4e6f7468;

  @override
  String toString() => 'Nothing';
}

/// Converts a nullable nonnullable payload without conflating Some(null) and Nothing.
CottOption<T> optionFromNullable<T extends Object>(T? value) =>
    value == null ? Nothing<T>() : Some<T>(value);

/// The inverse of optionFromNullable; nullable Option payloads must be matched explicitly.
T? optionToNullable<T extends Object>(CottOption<T> value) {
  switch (value) {
    case Some<T>():
      // Never collapse Some(null), even if a caller circumvents static checking.
      final Object? payload = value.value;
      if (payload == null) {
        return CottRuntime.violation(
          'Some(null) has no lossless nullable representation',
          phase: 'validation',
          expected: 'a nonnull Option payload',
          actual: 'null',
        );
      }
      return value.value;
    case Nothing<T>():
      return null;
  }
}

sealed class CottResult<T, E> {
  const CottResult();
}

final class Ok<T, E> extends CottResult<T, E> {
  const Ok(this.value);
  final T value;

  @override
  bool operator ==(Object other) =>
      other is Ok<Object?, Object?> && CottRuntime.deepEqual(value, other.value);

  @override
  int get hashCode => CottRuntime.deepHash(value);

  @override
  String toString() => 'Ok($value)';
}

final class Err<T, E> extends CottResult<T, E> {
  const Err(this.error);
  final E error;

  @override
  bool operator ==(Object other) =>
      other is Err<Object?, Object?> && CottRuntime.deepEqual(error, other.error);

  @override
  int get hashCode => CottRuntime.deepHash(error);

  @override
  String toString() => 'Err($error)';
}

Never _immutableMutation(String type) =>
    throw UnsupportedError('$type is immutable');

final class CottList<T> extends ListBase<T> {
  CottList(Iterable<T> values) : _values = List<T>.unmodifiable(values);
  final List<T> _values;

  @override
  int get length => _values.length;

  @override
  set length(int value) => _immutableMutation('CottList');

  @override
  T operator [](int index) => _values[index];

  @override
  void operator []=(int index, T value) => _immutableMutation('CottList');

  @override
  bool operator ==(Object other) =>
      other is CottList<Object?> && CottRuntime.deepEqual(this, other);

  @override
  int get hashCode => CottRuntime.deepHash(this);

  @override
  String toString() => 'CottList($_values)';
}

Uint8List _copyBytes(Iterable<int> bytes, String path) {
  final values = List<int>.of(bytes);
  for (var index = 0; index < values.length; index += 1) {
    final value = values[index];
    if (value < 0 || value > 255) {
      CottRuntime.violation(
        '$path[$index] is outside unsigned 8-bit range',
        phase: 'validation',
        expected: '0..255',
        actual: '$value',
      );
    }
  }
  return Uint8List.fromList(values);
}

final class CottBytes extends ListBase<int> {
  CottBytes(Iterable<int> bytes) : _data = _copyBytes(bytes, r'$');
  factory CottBytes.fromHex(String hex) =>
      CottBytes(CottRuntime.bytesFromHex(hex));
  final Uint8List _data;

  @override
  int get length => _data.length;

  @override
  set length(int value) => _immutableMutation('CottBytes');

  @override
  int operator [](int index) => _data[index];

  @override
  void operator []=(int index, int value) => _immutableMutation('CottBytes');

  /// A zero-copy read-only view. Neither this view nor casts can expose storage.
  List<int> get readOnlyView => this;

  Uint8List toUint8List() => Uint8List.fromList(_data);

  @override
  bool operator ==(Object other) =>
      other is CottBytes && CottRuntime.deepEqual(this, other);

  @override
  int get hashCode => CottRuntime.deepHash(this);

  @override
  String toString() => 'CottBytes(${base64Encode(_data)})';
}

final class CottBuffer<N extends CottConst> extends ListBase<int> {
  CottBuffer(Iterable<int> bytes, this.dimension)
      : _data = _copyBytes(bytes, r'$') {
    final expected = CottRuntime.constLength(dimension, path: r'$.dimension');
    if (_data.length != expected) {
      CottRuntime.violation(
        'buffer length does not match its const witness',
        phase: 'validation',
        expected: '$expected',
        actual: '${_data.length}',
      );
    }
  }

  factory CottBuffer.fromHex(String hex, N dimension) =>
      CottBuffer(CottRuntime.bytesFromHex(hex), dimension);

  final Uint8List _data;
  final N dimension;

  @override
  int get length => _data.length;

  @override
  set length(int value) => _immutableMutation('CottBuffer');

  @override
  int operator [](int index) => _data[index];

  @override
  void operator []=(int index, int value) => _immutableMutation('CottBuffer');

  Uint8List toUint8List() => Uint8List.fromList(_data);

  @override
  bool operator ==(Object other) =>
      other is CottBuffer<CottConst> && CottRuntime.deepEqual(this, other);

  @override
  int get hashCode => CottRuntime.deepHash(this);
}

final class CottSet<T> extends SetBase<T> {
  CottSet(Iterable<T> values) {
    for (final candidate in values) {
      if (!_values.any((value) => CottRuntime.canonicalEqual(value, candidate))) {
        _values.add(candidate);
      }
    }
  }

  final List<T> _values = <T>[];

  @override
  int get length => _values.length;

  @override
  Iterator<T> get iterator => _values.iterator;

  @override
  bool contains(Object? element) =>
      _values.any((value) => CottRuntime.canonicalEqual(value, element));

  @override
  T? lookup(Object? element) {
    for (final value in _values) {
      if (CottRuntime.canonicalEqual(value, element)) return value;
    }
    return null;
  }

  @override
  Set<T> toSet() => Set<T>.unmodifiable(_values);

  @override
  Set<T> union(Set<T> other) => CottSet<T>(<T>[..._values, ...other]);

  @override
  Set<T> intersection(Set<Object?> other) =>
      CottSet<T>(_values.where(other.contains));

  @override
  Set<T> difference(Set<Object?> other) =>
      CottSet<T>(_values.where((value) => !other.contains(value)));

  @override
  void retainAll(Iterable<Object?> elements) => _immutableMutation('CottSet');

  @override
  bool add(T value) => _immutableMutation('CottSet');

  @override
  bool remove(Object? value) => _immutableMutation('CottSet');

  @override
  void clear() => _immutableMutation('CottSet');

  @override
  bool operator ==(Object other) =>
      other is CottSet<Object?> && CottRuntime.deepEqual(this, other);

  @override
  int get hashCode => CottRuntime.deepHash(this);

  @override
  String toString() => 'CottSet($_values)';
}

final class CottMapEntry<K, V> {
  const CottMapEntry(this.key, this.value);
  final K key;
  final V value;
}

class FrozenMap<K, V> extends MapBase<K, V> {
  FrozenMap(Map<K, V> values) : this.entries(values.entries);

  FrozenMap.entries(Iterable<MapEntry<K, V>> entries) {
    for (final entry in entries) {
      _add(entry.key, entry.value);
    }
  }

  FrozenMap.cottEntries(Iterable<CottMapEntry<K, V>> entries) {
    for (final entry in entries) {
      _add(entry.key, entry.value);
    }
  }

  void _add(K key, V value) {
    final prior = _entries.indexWhere(
      (candidate) => CottRuntime.canonicalEqual(candidate.key, key),
    );
    if (prior >= 0) _entries.removeAt(prior);
    _entries.add(CottMapEntry(key, value));
  }

  final List<CottMapEntry<K, V>> _entries = <CottMapEntry<K, V>>[];

  @override
  V? operator [](Object? key) {
    for (final entry in _entries) {
      if (CottRuntime.canonicalEqual(entry.key, key)) return entry.value;
    }
    return null;
  }

  @override
  Iterable<K> get keys => _entries.map((entry) => entry.key);

  @override
  bool containsKey(Object? key) =>
      _entries.any((entry) => CottRuntime.canonicalEqual(entry.key, key));

  @override
  void operator []=(K key, V value) => _immutableMutation('FrozenMap');

  @override
  V? remove(Object? key) => _immutableMutation('FrozenMap');

  @override
  void clear() => _immutableMutation('FrozenMap');

  @override
  bool operator ==(Object other) =>
      other is FrozenMap<Object?, Object?> && CottRuntime.deepEqual(this, other);

  @override
  int get hashCode => CottRuntime.deepHash(this);

  @override
  String toString() {
    final values = <K, V>{};
    for (final entry in _entries) {
      values[entry.key] = entry.value;
    }
    return 'FrozenMap($values)';
  }
}

final class CottMap<K, V> extends FrozenMap<K, V> {
  CottMap(Iterable<CottMapEntry<K, V>> entries) : super.cottEntries(entries);
  CottMap.fromMap(Map<K, V> values) : super(values);
}

final class CottKeywordArguments<T> extends FrozenMap<String, T> {
  CottKeywordArguments(Map<String, T> values) : super(values) {
    for (final key in keys) {
      CottRuntime.validateUnicode(key, path: r'$.key');
    }
  }
}

final class CottTuple extends ListBase<Object?> implements CottTupleValue {
  CottTuple(Iterable<Object?> values) : cottTupleElements = CottList(values);

  @override
  final CottList<Object?> cottTupleElements;

  @override
  int get length => cottTupleElements.length;

  @override
  set length(int value) => _immutableMutation('CottTuple');

  @override
  Object? operator [](int index) => cottTupleElements[index];

  @override
  void operator []=(int index, Object? value) => _immutableMutation('CottTuple');

  @override
  CottTuple cottRebuild(CottList<Object?> elements) => CottTuple(elements);

  @override
  bool operator ==(Object other) =>
      other is CottTupleValue && CottRuntime.deepEqual(this, other);

  @override
  int get hashCode => CottRuntime.deepHash(this);
}

final class CottArray<T, N extends CottConst> extends ListBase<T> {
  CottArray(Iterable<T> values, this.dimension) : _values = CottList(values) {
    final expected = CottRuntime.constLength(dimension, path: r'$.dimension');
    if (_values.length != expected) {
      CottRuntime.violation(
        'array length does not match its const witness',
        phase: 'validation',
        expected: '$expected',
        actual: '${_values.length}',
      );
    }
  }

  final CottList<T> _values;
  final N dimension;

  @override
  int get length => _values.length;

  @override
  set length(int value) => _immutableMutation('CottArray');

  @override
  T operator [](int index) => _values[index];

  @override
  void operator []=(int index, T value) => _immutableMutation('CottArray');

  @override
  bool operator ==(Object other) =>
      other is CottArray<Object?, CottConst> && CottRuntime.deepEqual(this, other);

  @override
  int get hashCode => CottRuntime.deepHash(this);
}

final class CottPath {
  CottPath(this.value) {
    CottRuntime.validateUnicode(value, path: r'$.path');
    if (value.codeUnits.contains(0)) {
      CottRuntime.violation('path contains NUL', phase: 'validation');
    }
    if (value.contains('\\')) {
      CottRuntime.violation(
        'portable paths use POSIX separators',
        phase: 'validation',
        actual: value,
      );
    }
  }

  final String value;
  bool get isAbsolute => value.startsWith('/');
  CottList<String> get segments =>
      CottList(value.split('/').where((part) => part.isNotEmpty));
  String get basename => segments.isEmpty ? '' : segments.last;

  CottPath get parent {
    final parts = List<String>.of(segments);
    if (parts.isNotEmpty) parts.removeLast();
    final prefix = isAbsolute ? '/' : '';
    return CottPath('$prefix${parts.join('/')}');
  }

  CottPath join(String child) {
    CottRuntime.validateUnicode(child, path: r'$.child');
    if (child.isEmpty || child.startsWith('/') || child.contains('\\')) {
      CottRuntime.violation(
        'joined path must be a non-empty relative POSIX path',
        phase: 'validation',
        actual: child,
      );
    }
    final separator = value.isEmpty || value.endsWith('/') ? '' : '/';
    return CottPath('$value$separator$child');
  }

  @override
  bool operator ==(Object other) => other is CottPath && value == other.value;

  @override
  int get hashCode => value.hashCode;

  @override
  String toString() => value;
}

final class Opaque<Tag extends CottOpaqueTag> {
  Opaque._(this.tag, this._payload) {
    CottRuntime.validateUnicode(tag.tag, path: r'$.tag');
    if (tag.tag.isEmpty) {
      CottRuntime.violation('opaque tag must be non-empty', phase: 'validation');
    }
  }

  factory Opaque.of(Tag tag, Object payload) => Opaque._(tag, payload);

  final Tag tag;
  final Object _payload;
  Object unwrap() => _payload;

  @override
  bool operator ==(Object other) =>
      other is Opaque<CottOpaqueTag> &&
      identical(tag, other.tag) &&
      identical(_payload, other._payload);

  @override
  int get hashCode => Object.hash(identityHashCode(tag), identityHashCode(_payload));
}

final class CottTrait<T extends Object> {
  CottTrait._(this.id, this._predicate) {
    CottRuntime.validateUnicode(id, path: r'$.trait');
    if (id.isEmpty) {
      CottRuntime.violation('trait identity must be non-empty', phase: 'validation');
    }
  }

  factory CottTrait.exact(String id, Type type) =>
      CottTrait._(id, (value) => value.runtimeType == type);

  factory CottTrait.checked(String id, bool Function(Object) accepts) =>
      CottTrait._(id, accepts);

  final String id;
  final bool Function(Object) _predicate;

  bool accepts(Object value) =>
      _predicate(value) &&
      value is CottTraitCarrier &&
      value.cottTraits.any((trait) => identical(trait, this));

  @override
  bool operator ==(Object other) => identical(this, other);

  @override
  int get hashCode => identityHashCode(this);

  @override
  String toString() => 'CottTrait($id)';
}

final class Dyn<T extends Object> {
  Dyn._(this.value, this.trait) {
    if (!trait.accepts(value)) {
      CottRuntime.violation(
        'dynamic value does not carry the requested exact trait',
        phase: 'validation',
        expected: trait.id,
        actual: value.runtimeType.toString(),
      );
    }
  }

  factory Dyn.of(T value, CottTrait<T> trait) => Dyn._(value, trait);

  final T value;
  final CottTrait<T> trait;

  @override
  bool operator ==(Object other) => identical(this, other);

  @override
  int get hashCode => identityHashCode(this);
}

final class CottFactory<T extends Object> {
  const CottFactory._(this.type, this._construct);

  factory CottFactory.of(
    Type type,
    T Function(
      CottList<Object?> positional,
      CottMap<String, Object?> named,
    ) construct,
  ) =>
      CottFactory._(type, construct);

  factory CottFactory.zero(Type type, T Function() construct) =>
      CottFactory._(type, (positional, named) {
        if (positional.isNotEmpty || named.isNotEmpty) {
          return CottRuntime.violation(
            'zero-argument factory received arguments',
            phase: 'factory',
            expected: 'no arguments',
          );
        }
        return construct();
      });

  final Type type;
  final T Function(
    CottList<Object?> positional,
    CottMap<String, Object?> named,
  ) _construct;

  T construct(
    CottList<Object?> positional,
    CottMap<String, Object?> named,
  ) =>
      _construct(positional, named);

  @override
  bool operator ==(Object other) =>
      other is CottFactory<Object> && type == other.type;

  @override
  int get hashCode => type.hashCode;
}

sealed class JsonValue {
  const JsonValue();
}

final class JsonNull extends JsonValue {
  const JsonNull();

  @override
  bool operator ==(Object other) => other is JsonNull;

  @override
  int get hashCode => 0x4a4e554c;
}

final class JsonBoolean extends JsonValue {
  const JsonBoolean(this.value);
  final bool value;

  @override
  bool operator ==(Object other) => other is JsonBoolean && value == other.value;

  @override
  int get hashCode => value.hashCode;
}

final class JsonInteger extends JsonValue {
  JsonInteger(this.value) {
    CottRuntime.checkInt(value, signed: true, bits: 64, path: r'$.value');
  }
  final BigInt value;

  @override
  bool operator ==(Object other) => other is JsonInteger && value == other.value;

  @override
  int get hashCode => value.hashCode;
}

final class JsonFloat extends JsonValue {
  JsonFloat(this.value) {
    CottRuntime.validateF64(value, path: r'$.value');
  }
  final double value;

  @override
  bool operator ==(Object other) => other is JsonFloat && value == other.value;

  @override
  int get hashCode => value == 0.0 ? 0.0.hashCode : value.hashCode;
}

final class JsonString extends JsonValue {
  JsonString(this.value) {
    CottRuntime.validateUnicode(value, path: r'$.value');
  }
  final String value;

  @override
  bool operator ==(Object other) => other is JsonString && value == other.value;

  @override
  int get hashCode => value.hashCode;
}

final class JsonArray extends JsonValue {
  JsonArray(Iterable<JsonValue> values) : value = CottList(values) {
    CottRuntime.abi(this, CottTypes.json);
  }
  final CottList<JsonValue> value;

  @override
  bool operator ==(Object other) =>
      other is JsonArray && CottRuntime.deepEqual(value, other.value);

  @override
  int get hashCode => CottRuntime.deepHash(value);
}

final class JsonObject extends JsonValue {
  JsonObject(Map<String, JsonValue> values) : value = CottMap.fromMap(values) {
    CottRuntime.abi(this, CottTypes.json);
  }

  JsonObject.entries(Iterable<MapEntry<String, JsonValue>> values)
      : value = CottMap([
          for (final entry in values) CottMapEntry(entry.key, entry.value),
        ]) {
    CottRuntime.abi(this, CottTypes.json);
  }

  final CottMap<String, JsonValue> value;

  @override
  bool operator ==(Object other) =>
      other is JsonObject && CottRuntime.deepEqual(value, other.value);

  @override
  int get hashCode => CottRuntime.deepHash(value);
}

final class _VisitKey {
  const _VisitKey(this.value, this.type);
  final Object? value;
  final Object type;

  @override
  bool operator ==(Object other) =>
      other is _VisitKey && identical(value, other.value) && identical(type, other.type);

  @override
  int get hashCode => Object.hash(identityHashCode(value), identityHashCode(type));
}

final class _Traversal {
  _Traversal(this.normalizeOnly);
  final bool normalizeOnly;
  final Set<_VisitKey> _active = <_VisitKey>{};
  final Map<_VisitKey, Object?> _completed = <_VisitKey, Object?>{};
  int _nodes = 0;

  T transform<T>(Object? value, CottType<T> type, String path, int depth) {
    if (depth > 64) {
      CottRuntime.violation('$path exceeds ABI traversal depth 64', phase: 'validation');
    }
    _nodes += 1;
    if (_nodes > 1024) {
      CottRuntime.violation('$path exceeds ABI traversal node limit 1024', phase: 'validation');
    }
    final key = _VisitKey(value, type);
    if (_completed.containsKey(key)) return _completed[key] as T;
    if (!_active.add(key)) {
      CottRuntime.violation('$path contains an active value cycle', phase: 'validation');
    }
    try {
      final result = normalizeOnly
          ? type._normalizeDirect(value, path, this, depth)
          : type._validateDirect(value, path, this, depth);
      _active.remove(key);
      _completed[key] = result;
      return result as T;
    } catch (_) {
      _active.remove(key);
      rethrow;
    }
  }
}

final class _Adaptation {
  final Set<_VisitKey> _active = <_VisitKey>{};
  final Map<_VisitKey, Object?> _completed = <_VisitKey, Object?>{};
  int _nodes = 0;

  Object? transform(
    Object? value,
    CottType<Object?> type,
    RuntimeValidation mode,
    String path,
    int depth,
  ) {
    if (depth > 64) {
      CottRuntime.violation('$path exceeds ABI adaptation depth 64', phase: 'validation');
    }
    _nodes += 1;
    if (_nodes > 1024) {
      CottRuntime.violation('$path exceeds ABI adaptation node limit 1024', phase: 'validation');
    }
    final key = _VisitKey(value, type._adaptationIdentity);
    if (_completed.containsKey(key)) return _completed[key];
    if (!_active.add(key)) {
      CottRuntime.violation('$path contains an active value cycle', phase: 'validation');
    }
    try {
      final result = type._adaptDirect(value, mode, path, this, depth);
      _active.remove(key);
      _completed[key] = result;
      return result;
    } catch (_) {
      _active.remove(key);
      rethrow;
    }
  }
}

sealed class CottType<T> {
  const CottType(this.displayName);
  final String displayName;

  Object? _validateDirect(Object? value, String path, _Traversal state, int depth);

  Object? _normalizeDirect(Object? value, String path, _Traversal state, int depth) => value;

  Object get _adaptationIdentity => this;

  Object? _adaptDirect(
    Object? value,
    RuntimeValidation mode,
    String path,
    _Adaptation state,
    int depth,
  ) => value;

  /// Whether this reified Cott descriptor is a subtype of [expected].
  /// Dart's own covariant generic test is deliberately not consulted.
  bool isSubtypeOf(CottType<Object?> expected) =>
      identical(expected, CottTypes.any) ||
      identical(this, CottTypes.never) ||
      identical(this, expected);

  /// Whether this descriptor is, or transitively implements, nominal [identity].
  /// Compiler-provided descriptor identities are authoritative, not Dart types.
  bool satisfiesNominal(String identity) => identical(this, CottTypes.never);

  @override
  String toString() => displayName;
}

typedef _Validate = Object? Function(Object?, String, _Traversal, int);
typedef _Adapt = Object? Function(Object?, RuntimeValidation, String, _Adaptation, int);

class _CallbackType<T> extends CottType<T> {
  _CallbackType(
    super.displayName,
    this._validate, {
    _Validate? normalize,
    _Adapt? adapt,
    Object? adaptationIdentity,
  })  : _normalize = normalize,
        _adapt = adapt,
        _identity = adaptationIdentity;

  final _Validate _validate;
  final _Validate? _normalize;
  final _Adapt? _adapt;
  final Object? _identity;

  @override
  Object? _validateDirect(Object? value, String path, _Traversal state, int depth) =>
      _validate(value, path, state, depth);

  @override
  Object? _normalizeDirect(Object? value, String path, _Traversal state, int depth) =>
      _normalize?.call(value, path, state, depth) ?? value;

  @override
  Object get _adaptationIdentity => _identity ?? this;

  @override
  Object? _adaptDirect(
    Object? value,
    RuntimeValidation mode,
    String path,
    _Adaptation state,
    int depth,
  ) => _adapt?.call(value, mode, path, state, depth) ?? value;
}

final class _NominalType<T> extends _CallbackType<T> {
  _NominalType(
    String displayName,
    _Validate validate, {
    required this.identity,
    required this.relationSeal,
    required Iterable<CottType<Object?>> arguments,
    required Iterable<CottVariance> variances,
    Iterable<CottType<Object?>> supertypes = const [],
    _Validate? normalize,
    _Adapt? adapt,
  })  : arguments = CottList(arguments),
        variances = CottList(variances),
        supertypes = CottList(supertypes),
        super(displayName, validate, normalize: normalize, adapt: adapt) {
    if (this.arguments.length != this.variances.length) {
      CottRuntime.violation(
        'nominal descriptor argument/variance arity mismatch',
        phase: 'validation',
        actual: identity,
      );
    }
  }

  final String identity;
  final Object relationSeal;
  final CottList<CottType<Object?>> arguments;
  final CottList<CottVariance> variances;
  final CottList<CottType<Object?>> supertypes;

  @override
  bool isSubtypeOf(CottType<Object?> expected) {
    if (super.isSubtypeOf(expected)) return true;
    if (supertypes.any((type) => type.isSubtypeOf(expected))) return true;
    if (expected is! _NominalType<Object?> ||
        identity != expected.identity ||
        !(identical(relationSeal, expected.relationSeal) ||
            (relationSeal is Type &&
                expected.relationSeal is Type &&
                relationSeal == expected.relationSeal)) ||
        arguments.length != expected.arguments.length) {
      return false;
    }
    for (var index = 0; index < arguments.length; index += 1) {
      final actual = arguments[index];
      final wanted = expected.arguments[index];
      final matches = switch (expected.variances[index]) {
        CottVariance.invariant =>
          actual.isSubtypeOf(wanted) && wanted.isSubtypeOf(actual),
        CottVariance.covariant => actual.isSubtypeOf(wanted),
        CottVariance.contravariant => wanted.isSubtypeOf(actual),
      };
      if (!matches) return false;
    }
    return true;
  }

  @override
  bool satisfiesNominal(String expectedIdentity) =>
      identity == expectedIdentity ||
      supertypes.any((type) => type.satisfiesNominal(expectedIdentity));
}

final class _DeferredType<T> extends CottType<T> {
  _DeferredType(super.displayName, this._provider);
  final CottType<T> Function() _provider;
  CottType<T>? _resolved;
  bool _resolving = false;

  CottType<T> get _resolvedType => _resolve(0);

  CottType<T> _resolve(int depth) {
    final cached = _resolved;
    if (cached != null) return cached;
    if (_resolving || depth > 64) {
      CottRuntime.violation('cyclic or excessively deep deferred descriptor', phase: 'validation');
    }
    _resolving = true;
    try {
      final provided = _provider();
      final resolved = provided is _DeferredType<T>
          ? provided._resolve(depth + 1)
          : provided;
      return _resolved = resolved;
    } finally {
      _resolving = false;
    }
  }

  @override
  Object? _validateDirect(
    Object? value,
    String path,
    _Traversal state,
    int depth,
  ) =>
      _resolvedType._validateDirect(value, path, state, depth);

  @override
  Object? _normalizeDirect(
    Object? value,
    String path,
    _Traversal state,
    int depth,
  ) =>
      _resolvedType._normalizeDirect(value, path, state, depth);

  @override
  Object get _adaptationIdentity => _resolvedType._adaptationIdentity;

  @override
  Object? _adaptDirect(
    Object? value,
    RuntimeValidation mode,
    String path,
    _Adaptation state,
    int depth,
  ) =>
      _resolvedType._adaptDirect(value, mode, path, state, depth);

  @override
  bool isSubtypeOf(CottType<Object?> expected) {
    if (identical(this, expected)) return true;
    final target = expected is _DeferredType<Object?>
        ? expected._resolvedType
        : expected;
    return (_resolvedType as CottType<Object?>).isSubtypeOf(target);
  }

  @override
  bool satisfiesNominal(String identity) =>
      (_resolvedType as CottType<Object?>).satisfiesNominal(identity);
}

final class CottNominalField<T extends Object> {
  const CottNominalField(this.name, this.type, this.read);
  final String name;
  final CottType<Object?> type;
  final Object? Function(T) read;
}

final class CottTypes {
  CottTypes._();

  static Never _mismatch(String path, String expected, Object? value) =>
      CottRuntime.violation(
        '$path does not match ABI type',
        phase: 'validation',
        expected: expected,
        actual: value?.runtimeType.toString() ?? 'null',
      );

  static final CottType<Object?> any = _CallbackType<Object?>('Any', (value, _, __, ___) => value);
  static final CottType<Never> never = _CallbackType<Never>(
    'Never',
    (value, path, _, __) => _mismatch(path, 'Never', value),
  );
  static final CottType<bool> boolean = _CallbackType<bool>(
    'Bool',
    (value, path, _, __) => value is bool ? value : _mismatch(path, 'Bool', value),
  );

  static CottType<int> _smallInteger(CottIntKind kind) => _CallbackType<int>(
        kind.name.toUpperCase(),
        (value, path, _, __) {
          if (value is! int) return _mismatch(path, kind.name.toUpperCase(), value);
          CottRuntime.checkInt(BigInt.from(value), signed: kind.signed, bits: kind.bits, path: path);
          return value;
        },
      );

  static CottType<BigInt> _bigInteger(CottIntKind kind) => _CallbackType<BigInt>(
        kind.name.toUpperCase(),
        (value, path, _, __) {
          if (value is! BigInt) return _mismatch(path, kind.name.toUpperCase(), value);
          return CottRuntime.checkInt(value, signed: kind.signed, bits: kind.bits, path: path);
        },
      );

  static final CottType<int> i8 = _smallInteger(CottIntKind.i8);
  static final CottType<int> i16 = _smallInteger(CottIntKind.i16);
  static final CottType<int> i32 = _smallInteger(CottIntKind.i32);
  static final CottType<BigInt> i64 = _bigInteger(CottIntKind.i64);
  static final CottType<int> u8 = _smallInteger(CottIntKind.u8);
  static final CottType<int> u16 = _smallInteger(CottIntKind.u16);
  static final CottType<int> u32 = _smallInteger(CottIntKind.u32);
  static final CottType<BigInt> u64 = _bigInteger(CottIntKind.u64);

  static final CottType<double> f32 = _CallbackType<double>(
    'F32',
    (value, path, _, __) => value is double
        ? CottRuntime.normalizeF32(value, path: path)
        : _mismatch(path, 'F32', value),
    normalize: (value, path, _, __) =>
        value is double ? CottRuntime.normalizeF32(value, path: path) : value,
  );
  static final CottType<double> f64 = _CallbackType<double>(
    'F64',
    (value, path, _, __) => value is double
        ? CottRuntime.validateF64(value, path: path)
        : _mismatch(path, 'F64', value),
  );
  static final CottType<String> string = _CallbackType<String>(
    'String',
    (value, path, _, __) => value is String
        ? CottRuntime.validateUnicode(value, path: path)
        : _mismatch(path, 'String', value),
  );
  static final CottType<CottBytes> bytes = _CallbackType<CottBytes>(
    'Bytes',
    (value, path, _, __) => value is CottBytes ? value : _mismatch(path, 'CottBytes', value),
  );
  static final CottType<CottPath> path = _CallbackType<CottPath>(
    'Path',
    (value, path, _, __) => value is CottPath ? value : _mismatch(path, 'CottPath', value),
  );
  static final CottType<CottUnit> unit = _CallbackType<CottUnit>(
    'Unit',
    (value, path, _, __) => identical(value, CottUnit.instance)
        ? value
        : _mismatch(path, 'CottUnit.instance', value),
  );

  static final CottType<JsonValue> json = deferred<JsonValue>('JsonValue', () => _jsonType());

  static CottType<Object?> integer(CottIntKind kind) => switch (kind) {
        CottIntKind.i8 => i8,
        CottIntKind.i16 => i16,
        CottIntKind.i32 => i32,
        CottIntKind.i64 => i64,
        CottIntKind.u8 => u8,
        CottIntKind.u16 => u16,
        CottIntKind.u32 => u32,
        CottIntKind.u64 => u64,
      } as CottType<Object?>;

  static CottType<T> deferred<T>(
    String name,
    CottType<T> Function() provider,
  ) =>
      _DeferredType<T>(name, provider);

  static CottType<CottOption<T>> option<T>(CottType<T> item) => _CallbackType<CottOption<T>>(
        'Option<$item>',
        (value, path, state, depth) {
          if (value is Nothing) return value;
          if (value is Some) {
            final next = state.transform(value.value, item, '$path.value', depth + 1);
            return identical(next, value.value) ? value : Some<T>(next);
          }
          return _mismatch(path, 'Option<$item>', value);
        },
        normalize: (value, path, state, depth) {
          if (value is! Some) return value;
          final next = state.transform(value.value, item, '$path.value', depth + 1);
          return identical(next, value.value) ? value : Some<T>(next);
        },
        adapt: (value, mode, path, state, depth) {
          if (value is! Some) return value;
          final next = state.transform(
            value.value,
            item as CottType<Object?>,
            mode,
            '$path.value',
            depth + 1,
          );
          return identical(next, value.value) ? value : Some<Object?>(next);
        },
      );

  static CottType<CottResult<T, E>> result<T, E>(CottType<T> ok, CottType<E> err) =>
      _CallbackType<CottResult<T, E>>(
        'Result<$ok, $err>',
        (value, path, state, depth) {
          if (value is Ok) {
            final next = state.transform(value.value, ok, '$path.value', depth + 1);
            return identical(next, value.value) ? value : Ok<T, E>(next);
          }
          if (value is Err) {
            final next = state.transform(value.error, err, '$path.error', depth + 1);
            return identical(next, value.error) ? value : Err<T, E>(next);
          }
          return _mismatch(path, 'Result<$ok, $err>', value);
        },
        normalize: (value, path, state, depth) {
          if (value is Ok) {
            final next = state.transform(value.value, ok, '$path.value', depth + 1);
            return identical(next, value.value) ? value : Ok<T, E>(next);
          }
          if (value is Err) {
            final next = state.transform(value.error, err, '$path.error', depth + 1);
            return identical(next, value.error) ? value : Err<T, E>(next);
          }
          return value;
        },
        adapt: (value, mode, path, state, depth) {
          if (value is Ok) {
            final next = state.transform(
              value.value,
              ok as CottType<Object?>,
              mode,
              '$path.value',
              depth + 1,
            );
            return identical(next, value.value) ? value : Ok<Object?, Object?>(next);
          }
          if (value is Err) {
            final next = state.transform(
              value.error,
              err as CottType<Object?>,
              mode,
              '$path.error',
              depth + 1,
            );
            return identical(next, value.error) ? value : Err<Object?, Object?>(next);
          }
          return value;
        },
      );

  static CottType<CottList<T>> list<T>(CottType<T> item) =>
      _sequence<CottList<T>, T>('CottList<$item>', item, (value) => value is CottList ? value : null, CottList<T>.new);

  static CottType<CottSet<T>> set<T>(CottType<T> item) =>
      _sequence<CottSet<T>, T>('CottSet<$item>', item, (value) => value is CottSet ? value : null, CottSet<T>.new);

  static CottType<C> _sequence<C, T>(
    String name,
    CottType<T> item,
    Iterable<Object?>? Function(Object?) cast,
    C Function(Iterable<T>) build,
  ) =>
      _CallbackType<C>(
        name,
        (value, path, state, depth) =>
            _transformSequence(value, path, state, depth, item, cast, build, true),
        normalize: (value, path, state, depth) =>
            _transformSequence(value, path, state, depth, item, cast, build, false),
        adapt: (value, mode, path, state, depth) {
          final sequence = cast(value);
          if (sequence == null) return value;
          var changed = false;
          var index = 0;
          final result = <T>[];
          for (final raw in sequence) {
            final next = state.transform(
              raw,
              item as CottType<Object?>,
              mode,
              '$path[$index]',
              depth + 1,
            ) as T;
            result.add(next);
            changed = changed || !identical(next, raw);
            index += 1;
          }
          return changed ? build(result) : value;
        },
      );

  static Object? _transformSequence<C, T>(
    Object? value,
    String path,
    _Traversal state,
    int depth,
    CottType<T> item,
    Iterable<Object?>? Function(Object?) cast,
    C Function(Iterable<T>) build,
    bool strict,
  ) {
    final sequence = cast(value);
    if (sequence == null) return strict ? _mismatch(path, 'immutable sequence', value) : value;
    var changed = false;
    var index = 0;
    final result = <T>[];
    for (final raw in sequence) {
      final next = state.transform(raw, item, '$path[$index]', depth + 1);
      result.add(next);
      changed = changed || !identical(next, raw);
      index += 1;
    }
    return changed ? build(result) : value;
  }

  static CottType<CottMap<K, V>> map<K, V>(CottType<K> key, CottType<V> valueType) =>
      _CallbackType<CottMap<K, V>>(
        'CottMap<$key, $valueType>',
        (value, path, state, depth) =>
            _transformMap(value, path, state, depth, key, valueType, true),
        normalize: (value, path, state, depth) =>
            _transformMap(value, path, state, depth, key, valueType, false),
        adapt: (value, mode, path, state, depth) {
          if (value is! CottMap) return value;
          var changed = false;
          final entries = <MapEntry<K, V>>[];
          for (final entry in value.entries) {
            final nextKey = state.transform(
              entry.key,
              key as CottType<Object?>,
              mode,
              '$path.key',
              depth + 1,
            ) as K;
            final nextValue = state.transform(
              entry.value,
              valueType as CottType<Object?>,
              mode,
              '$path[${entry.key}]',
              depth + 1,
            ) as V;
            changed = changed || !identical(nextKey, entry.key) || !identical(nextValue, entry.value);
            entries.add(MapEntry(nextKey, nextValue));
          }
          return changed
              ? CottMap<K, V>([
                  for (final entry in entries)
                    CottMapEntry(entry.key, entry.value),
                ])
              : value;
        },
      );

  static Object? _transformMap<K, V>(
    Object? value,
    String path,
    _Traversal state,
    int depth,
    CottType<K> key,
    CottType<V> valueType,
    bool strict,
  ) {
    if (value is! CottMap) {
      return strict ? _mismatch(path, 'CottMap<$key, $valueType>', value) : value;
    }
    var changed = false;
    final entries = <MapEntry<K, V>>[];
    for (final entry in value.entries) {
      final nextKey = state.transform(entry.key, key, '$path.key', depth + 1);
      final nextValue = state.transform(entry.value, valueType, '$path[${entry.key}]', depth + 1);
      changed = changed || !identical(nextKey, entry.key) || !identical(nextValue, entry.value);
      entries.add(MapEntry(nextKey, nextValue));
    }
    return changed
        ? CottMap<K, V>([
            for (final entry in entries) CottMapEntry(entry.key, entry.value),
          ])
        : value;
  }

  static CottType<CottKeywordArguments<T>> keywordArguments<T>(CottType<T> item) =>
      _CallbackType<CottKeywordArguments<T>>(
        'KeywordArguments<$item>',
        (value, path, state, depth) {
          if (value is! CottKeywordArguments) return _mismatch(path, 'KeywordArguments<$item>', value);
          final result = <String, T>{};
          var changed = false;
          for (final entry in value.entries) {
            CottRuntime.validateUnicode(entry.key, path: '$path.key');
            final next = state.transform(entry.value, item, '$path[${entry.key}]', depth + 1);
            result[entry.key] = next;
            changed = changed || !identical(next, entry.value);
          }
          return changed ? CottKeywordArguments<T>(result) : value;
        },
        normalize: (value, path, state, depth) {
          if (value is! CottKeywordArguments) return value;
          final result = <String, T>{};
          var changed = false;
          for (final entry in value.entries) {
            final next = state.transform(entry.value, item, '$path[${entry.key}]', depth + 1);
            result[entry.key] = next;
            changed = changed || !identical(next, entry.value);
          }
          return changed ? CottKeywordArguments<T>(result) : value;
        },
        adapt: (value, mode, path, state, depth) {
          if (value is! CottKeywordArguments) return value;
          final result = <String, T>{};
          var changed = false;
          for (final entry in value.entries) {
            final next = state.transform(
              entry.value,
              item as CottType<Object?>,
              mode,
              '$path[${entry.key}]',
              depth + 1,
            ) as T;
            result[entry.key] = next;
            changed = changed || !identical(next, entry.value);
          }
          return changed ? CottKeywordArguments<T>(result) : value;
        },
      );

  static CottType<T> tuple<T extends CottTupleValue>(
    List<CottType<Object?>> items,
  ) =>
      _CallbackType<T>(
        'Tuple<${items.join(', ')}>',
        (value, path, state, depth) => _transformTuple(value, path, state, depth, items, true),
        normalize: (value, path, state, depth) =>
            _transformTuple(value, path, state, depth, items, false),
        adapt: (value, mode, path, state, depth) {
          if (value is! CottTupleValue || value.cottTupleElements.length != items.length) return value;
          var changed = false;
          final result = <Object?>[];
          for (var index = 0; index < items.length; index += 1) {
            final raw = value.cottTupleElements[index];
            final next = state.transform(raw, items[index], mode, '$path[$index]', depth + 1);
            result.add(next);
            changed = changed || !identical(next, raw);
          }
          return changed ? value.cottRebuild(CottList(result)) : value;
        },
      );

  static Object? _transformTuple(
    Object? value,
    String path,
    _Traversal state,
    int depth,
    List<CottType<Object?>> items,
    bool strict,
  ) {
    if (value is! CottTupleValue) return strict ? _mismatch(path, 'tuple', value) : value;
    if (value.cottTupleElements.length != items.length) {
      return strict ? _mismatch(path, 'tuple of length ${items.length}', value) : value;
    }
    var changed = false;
    final result = <Object?>[];
    for (var index = 0; index < items.length; index += 1) {
      final raw = value.cottTupleElements[index];
      final next = state.transform(raw, items[index], '$path[$index]', depth + 1);
      result.add(next);
      changed = changed || !identical(next, raw);
    }
    return changed ? value.cottRebuild(CottList(result)) : value;
  }

  static CottType<CottArray<T, N>> array<T, N extends CottConst>(
    CottType<T> item,
    int length, {
    N? witness,
  }) =>
      _arrayDescriptor(item, length, witness);

  static CottType<CottArray<T, N>> arrayParameterized<T, N extends CottConst>(
    CottType<T> item,
    N witness,
    CottIntKind kind,
  ) {
    CottRuntime.validateConst(witness, kind);
    return _arrayDescriptor(item, CottRuntime.constLength(witness), witness);
  }

  static CottType<CottArray<T, N>> _arrayDescriptor<T, N extends CottConst>(
    CottType<T> item,
    int expectedLength,
    N? witness,
  ) {
    if (expectedLength < 0) {
      CottRuntime.violation('array length must be non-negative', phase: 'validation');
    }
    return _CallbackType<CottArray<T, N>>(
      'Array<$item, $expectedLength>',
      (value, path, state, depth) =>
          _transformArray(value, path, state, depth, item, expectedLength, witness, true),
      normalize: (value, path, state, depth) =>
          _transformArray(value, path, state, depth, item, expectedLength, witness, false),
      adapt: (value, mode, path, state, depth) {
        if (value is! CottArray) return value;
        final result = <T>[];
        var changed = false;
        for (var index = 0; index < value.length; index += 1) {
          final raw = value[index];
          final next = state.transform(
            raw,
            item as CottType<Object?>,
            mode,
            '$path[$index]',
            depth + 1,
          ) as T;
          result.add(next);
          changed = changed || !identical(next, raw);
        }
        return changed ? CottArray<T, N>(result, value.dimension as N) : value;
      },
    );
  }

  static Object? _transformArray<T, N extends CottConst>(
    Object? value,
    String path,
    _Traversal state,
    int depth,
    CottType<T> item,
    int expectedLength,
    N? witness,
    bool strict,
  ) {
    if (value is! CottArray) return strict ? _mismatch(path, 'CottArray', value) : value;
    final actualLength = CottRuntime.constLength(value.dimension, path: '$path.dimension');
    if (actualLength != value.length || actualLength != expectedLength) {
      return strict ? _mismatch(path, 'Array<$item, $expectedLength>', value) : value;
    }
    if (witness != null && !CottRuntime.sameConst(value.dimension, witness)) {
      return strict ? _mismatch('$path.dimension', witness.runtimeType.toString(), value.dimension) : value;
    }
    final result = <T>[];
    var changed = false;
    for (var index = 0; index < value.length; index += 1) {
      final raw = value[index];
      final next = state.transform(raw, item, '$path[$index]', depth + 1);
      result.add(next);
      changed = changed || !identical(next, raw);
    }
    return changed ? CottArray<T, N>(result, value.dimension as N) : value;
  }

  static CottType<CottBuffer<N>> buffer<N extends CottConst>(int length, {N? witness}) =>
      _bufferDescriptor(length, witness);

  static CottType<CottBuffer<N>> bufferParameterized<N extends CottConst>(
    N witness,
    CottIntKind kind,
  ) {
    CottRuntime.validateConst(witness, kind);
    return _bufferDescriptor(CottRuntime.constLength(witness), witness);
  }

  static CottType<CottBuffer<N>> _bufferDescriptor<N extends CottConst>(int length, N? witness) =>
      _CallbackType<CottBuffer<N>>(
        'Buffer<$length>',
        (value, path, _, __) {
          if (value is! CottBuffer || value.length != length) {
            return _mismatch(path, 'Buffer<$length>', value);
          }
          if (witness != null && !CottRuntime.sameConst(value.dimension, witness)) {
            return _mismatch('$path.dimension', witness.runtimeType.toString(), value.dimension);
          }
          return value;
        },
      );

  static CottType<Opaque<Tag>> opaque<Tag extends CottOpaqueTag>(Tag tag) =>
      _CallbackType<Opaque<Tag>>(
        'Opaque<${tag.tag}>',
        (value, path, _, __) => value is Opaque && identical(value.tag, tag)
            ? value
            : _mismatch(path, 'Opaque<${tag.tag}>', value),
      );

  static CottType<Dyn<T>> dyn<T extends Object>(CottTrait<T> trait) =>
      _CallbackType<Dyn<T>>(
        'Dyn<${trait.id}>',
        (value, path, _, __) => value is Dyn && identical(value.trait, trait) && trait.accepts(value.value)
            ? value
            : _mismatch(path, 'Dyn<${trait.id}>', value),
      );

  static CottType<CottFactory<T>> factory<T extends Object>(Type type) =>
      _CallbackType<CottFactory<T>>(
        'Factory<$type>',
        (value, path, _, __) => value is CottFactory && value.type == type
            ? value
            : _mismatch(path, 'Factory<$type>', value),
      );

  static CottType<T> external<T>(
    String name,
    bool Function(Object?) accepts, {
    Iterable<CottType<Object?>> arguments = const [],
    Iterable<CottVariance> variances = const [],
    Iterable<CottType<Object?>> supertypes = const [],
    Object? identityWitness,
    Iterable<CottType<Object?>> Function(Object value)? observeArguments,
  }) {
    final expected = List<CottType<Object?>>.of(arguments);
    final declaredVariances = List<CottVariance>.of(variances);
    if (declaredVariances.contains(CottVariance.contravariant)) {
      CottRuntime.violation(
        'contravariant external generics require an explicit checked adapter',
        phase: 'validation',
        expected: 'a generated CottCheckedView',
        actual: name,
      );
    }
    return _NominalType<T>(
      name,
      (value, path, _, __) {
        if (!accepts(value)) return _mismatch(path, name, value);
        if (expected.isEmpty) return value;
        if (value == null || observeArguments == null) {
          return CottRuntime.violation(
            '$path external generic arguments are unobservable',
            phase: 'validation',
            expected: '$name with reified Cott arguments',
            actual: value?.runtimeType.toString() ?? 'null',
          );
        }
        final observed = List<CottType<Object?>>.of(observeArguments(value));
        if (!_argumentVectorsMatch(observed, expected, declaredVariances)) {
          return _mismatch(path, '$name with compatible Cott variance', value);
        }
        return value;
      },
      identity: name,
      arguments: expected,
      variances: declaredVariances,
      relationSeal: identityWitness ?? accepts,
      supertypes: supertypes,
    );
  }

  static CottType<T> literal<T>(T expected) => _CallbackType<T>(
        'Literal<$expected>',
        (value, path, _, __) => CottRuntime.canonicalEqual(value, expected)
            ? value
            : _mismatch(path, 'literal $expected', value),
      );

  static CottType<Object?> oneOf(List<CottType<Object?>> types) {
    if (types.isEmpty) {
      CottRuntime.violation('ABI union must have a member', phase: 'validation');
    }
    return _CallbackType<Object?>('Union<${types.join(', ')}>', (value, path, state, depth) {
      for (final type in types) {
        try {
          return state.transform(value, type, path, depth + 1);
        } on CottContractViolation {
          // A candidate mismatch does not prove the whole union mismatched.
        }
      }
      return _mismatch(path, 'Union<${types.join(', ')}>', value);
    });
  }

  static CottType<T> nominal<T extends Object>(
    String name,
    Type exactType,
    List<CottNominalField<T>> fields,
    T Function(CottList<Object?>) rebuild, {
    Iterable<CottType<Object?>> arguments = const [],
    Iterable<CottVariance> variances = const [],
    Iterable<CottType<Object?>> supertypes = const [],
  }) {
    final typeArguments = List<CottType<Object?>>.of(arguments);
    final declaredVariances = List<CottVariance>.of(variances);
    if (typeArguments.isNotEmpty || declaredVariances.isNotEmpty) {
      CottRuntime.violation(
        'generic nominal descriptors require a checked-view carrier',
        phase: 'validation',
        expected: 'CottTypes.checkedNominal',
        actual: name,
      );
    }
    late final _NominalType<T> descriptor;
    descriptor = _NominalType<T>(
      name,
      (value, path, state, depth) {
        if (!_genericArgumentsMatch(value, name, typeArguments, declaredVariances)) {
          return _mismatch(path, '$name with exact Cott generic arguments', value);
        }
        return _transformNominal(
          value,
          path,
          state,
          depth,
          name,
          exactType,
          fields,
          rebuild,
          true,
        );
      },
      identity: name,
      relationSeal: exactType,
      arguments: typeArguments,
      variances: declaredVariances,
      supertypes: supertypes,
      normalize: (value, path, state, depth) =>
          _transformNominal(value, path, state, depth, name, exactType, fields, rebuild, false),
      adapt: (value, mode, path, state, depth) {
        if (value is! T ||
            (value is! CottGenericValue && value.runtimeType != exactType)) {
          return value;
        }
        var changed = false;
        final result = <Object?>[];
        for (final field in fields) {
          final raw = field.read(value);
          final next = state.transform(raw, field.type, mode, '$path.${field.name}', depth + 1);
          result.add(next);
          changed = changed || !identical(next, raw);
        }
        return changed ? rebuild(CottList(result)) : value;
      },
    );
    return descriptor;
  }

  static CottType<V> checkedNominal<V extends CottCheckedView>(
    String name,
    List<CottNominalField<CottNominalCarrier>> fields,
    bool Function(CottNominalCarrier) acceptsCarrier,
    V Function(
      CottNominalCarrier carrier,
      CottList<CottType<Object?>> expectedArguments,
    ) buildView, {
    required bool Function(Object?) acceptsView,
    required Object viewSeal,
    required Iterable<CottType<Object?>> arguments,
    required Iterable<CottVariance> variances,
    Iterable<CottType<Object?>> supertypes = const [],
  }) {
    final expected = List<CottType<Object?>>.of(arguments);
    final declaredVariances = List<CottVariance>.of(variances);
    final viewArguments = CottList<CottType<Object?>>(expected);
    final access = CottViewAccess._(viewSeal);
    return _NominalType<V>(
      name,
      (value, path, state, depth) => _transformCheckedNominal(
        value,
        path,
        state,
        depth,
        name,
        fields,
        acceptsCarrier,
        acceptsView,
        buildView,
        expected,
        declaredVariances,
        viewArguments,
        access,
        true,
      ),
      identity: name,
      relationSeal: viewSeal,
      arguments: expected,
      variances: declaredVariances,
      supertypes: supertypes,
      normalize: (value, path, state, depth) => _transformCheckedNominal(
        value,
        path,
        state,
        depth,
        name,
        fields,
        acceptsCarrier,
        acceptsView,
        buildView,
        expected,
        declaredVariances,
        viewArguments,
        access,
        false,
      ),
      adapt: (value, mode, path, state, depth) {
        if (!acceptsView(value) || value is! CottCheckedView) return value;
        final carrier = value.cottCarrier(access);
        if (!acceptsCarrier(carrier)) return value;
        var changed = false;
        final result = <Object?>[];
        for (final field in fields) {
          final raw = field.read(carrier);
          final next = state.transform(
            raw,
            field.type,
            mode,
            '$path.${field.name}',
            depth + 1,
          );
          result.add(next);
          changed = changed || !identical(next, raw);
        }
        return changed
            ? buildView(carrier.cottRebuildCarrier(CottList(result)), viewArguments)
            : value;
      },
    );
  }

  static Object? _transformCheckedNominal<V extends CottCheckedView>(
    Object? value,
    String path,
    _Traversal state,
    int depth,
    String name,
    List<CottNominalField<CottNominalCarrier>> fields,
    bool Function(CottNominalCarrier) acceptsCarrier,
    bool Function(Object?) acceptsView,
    V Function(
      CottNominalCarrier carrier,
      CottList<CottType<Object?>> expectedArguments,
    ) buildView,
    List<CottType<Object?>> expected,
    List<CottVariance> variances,
    CottList<CottType<Object?>> viewArguments,
    CottViewAccess access,
    bool strict,
  ) {
    if (!acceptsView(value) || value is! CottCheckedView) {
      return _mismatch(path, '$name checked view', value);
    }
    final carrier = value.cottCarrier(access);
    if (!acceptsCarrier(carrier)) {
      return _mismatch(path, '$name checked view', value);
    }
    if (strict &&
        !_genericArgumentsMatch(carrier, name, expected, variances)) {
      return _mismatch(
        path,
        '$name with compatible explicit Cott arguments',
        value,
      );
    }
    var changed = false;
    final result = <Object?>[];
    for (final field in fields) {
      final raw = field.read(carrier);
      final next =
          state.transform(raw, field.type, '$path.${field.name}', depth + 1);
      result.add(next);
      changed = changed || !identical(next, raw);
    }
    final normalizedCarrier = changed
        ? carrier.cottRebuildCarrier(CottList(result))
        : carrier;
    // Always build a fresh statically typed view. Reusing [value] would make a
    // Dart covariant cast masquerade as Cott invariant/contravariant evidence.
    return buildView(normalizedCarrier, viewArguments);
  }

  static bool _genericArgumentsMatch(
    Object? value,
    String identity,
    List<CottType<Object?>> expected,
    List<CottVariance> variances,
  ) {
    if (expected.isEmpty && variances.isEmpty) return true;
    if (expected.length != variances.length ||
        value is! CottGenericValue ||
        value.cottGenericIdentity != identity ||
        value.cottTypeArguments.length != expected.length) {
      return false;
    }
    return _argumentVectorsMatch(
      value.cottTypeArguments,
      expected,
      variances,
    );
  }

  static bool _argumentVectorsMatch(
    Iterable<CottType<Object?>> actualArguments,
    List<CottType<Object?>> expected,
    List<CottVariance> variances,
  ) {
    final actualValues = List<CottType<Object?>>.of(actualArguments);
    if (actualValues.length != expected.length ||
        expected.length != variances.length) {
      return false;
    }
    for (var index = 0; index < expected.length; index += 1) {
      final actual = actualValues[index];
      final wanted = expected[index];
      final matches = switch (variances[index]) {
        CottVariance.invariant =>
          actual.isSubtypeOf(wanted) && wanted.isSubtypeOf(actual),
        CottVariance.covariant => actual.isSubtypeOf(wanted),
        CottVariance.contravariant => wanted.isSubtypeOf(actual),
      };
      if (!matches) return false;
    }
    return true;
  }

  static Object? _transformNominal<T extends Object>(
    Object? value,
    String path,
    _Traversal state,
    int depth,
    String name,
    Type exactType,
    List<CottNominalField<T>> fields,
    T Function(CottList<Object?>) rebuild,
    bool strict,
  ) {
    if (value is! T ||
        (value is! CottGenericValue && value.runtimeType != exactType)) {
      return strict ? _mismatch(path, name, value) : value;
    }
    var changed = false;
    final result = <Object?>[];
    for (final field in fields) {
      final raw = field.read(value);
      final next = state.transform(raw, field.type, '$path.${field.name}', depth + 1);
      result.add(next);
      changed = changed || !identical(next, raw);
    }
    return changed ? rebuild(CottList(result)) : value;
  }

  static CottType<CottIterator<T>> iterator<T>(CottType<T> item) =>
      _CallbackType<CottIterator<T>>(
        'Iterator<$item>',
        (value, path, _, __) => value is CottIterator || value is CottIteratorSource<T>
            ? value
            : _mismatch(path, 'Iterator<$item>', value),
        adapt: (value, mode, path, _, __) {
          if (value is CottIterator<T>) return value._matches(item, mode) ? value : _mismatch(path, 'compatible Iterator<$item>', value);
          if (value is CottIteratorSource<T>) return CottIterator(value, item, mode: mode, path: path);
          return value;
        },
      );

  static CottType<CottGenerator<Y, S, R>> generator<Y, S, R>(
    CottType<Y> yielded,
    CottType<S> sent,
    CottType<R> returned,
  ) =>
      _CallbackType<CottGenerator<Y, S, R>>(
        'Generator<$yielded, $sent, $returned>',
        (value, path, _, __) => value is CottGenerator || value is CottGeneratorSource<Y, S, R>
            ? value
            : _mismatch(path, 'Generator<$yielded, $sent, $returned>', value),
        adapt: (value, mode, path, _, __) {
          if (value is CottGenerator<Y, S, R>) {
            return value._matches(yielded, sent, returned, mode)
                ? value
                : _mismatch(path, 'compatible Generator<$yielded, $sent, $returned>', value);
          }
          if (value is CottGeneratorSource<Y, S, R>) {
            return CottGenerator(value, yielded, sent, returned, mode: mode, path: path);
          }
          return value;
        },
      );

  static CottType<CottAsyncIterator<T>> asyncIterator<T>(CottType<T> item) =>
      _CallbackType<CottAsyncIterator<T>>(
        'AsyncIterator<$item>',
        (value, path, _, __) => value is CottAsyncIterator || value is CottAsyncIteratorSource<T>
            ? value
            : _mismatch(path, 'AsyncIterator<$item>', value),
        adapt: (value, mode, path, _, __) {
          if (value is CottAsyncIterator<T>) return value._matches(item, mode) ? value : _mismatch(path, 'compatible AsyncIterator<$item>', value);
          if (value is CottAsyncIteratorSource<T>) return CottAsyncIterator(value, item, mode: mode, path: path);
          return value;
        },
      );

  static CottType<CottAsyncGenerator<Y, S, R>> asyncGenerator<Y, S, R>(
    CottType<Y> yielded,
    CottType<S> sent,
    CottType<R> returned,
  ) =>
      _CallbackType<CottAsyncGenerator<Y, S, R>>(
        'AsyncGenerator<$yielded, $sent, $returned>',
        (value, path, _, __) => value is CottAsyncGenerator || value is CottAsyncGeneratorSource<Y, S, R>
            ? value
            : _mismatch(path, 'AsyncGenerator<$yielded, $sent, $returned>', value),
        adapt: (value, mode, path, _, __) {
          if (value is CottAsyncGenerator<Y, S, R>) {
            return value._matches(yielded, sent, returned, mode)
                ? value
                : _mismatch(path, 'compatible AsyncGenerator<$yielded, $sent, $returned>', value);
          }
          if (value is CottAsyncGeneratorSource<Y, S, R>) {
            return CottAsyncGenerator(value, yielded, sent, returned, mode: mode, path: path);
          }
          return value;
        },
      );

  static CottType<Future<T>> future<T>(CottType<T> item) => _CallbackType<Future<T>>(
        'Future<$item>',
        (value, path, _, __) => value is Future<T> ? value : _mismatch(path, 'Future<$item>', value),
        adapt: (value, mode, path, _, __) => value is Future<T>
            ? value.then((resolved) => CottRuntime.returnValue(resolved, item, mode: mode, path: '$path.value'))
            : value,
      );

  static CottType<JsonValue> _jsonType() => _CallbackType<JsonValue>(
        'JsonValue',
        (value, path, state, depth) {
          if (value is JsonNull || value is JsonBoolean) return value;
          if (value is JsonInteger) {
            CottRuntime.checkInt(value.value, signed: true, bits: 64, path: '$path.value');
            return value;
          }
          if (value is JsonFloat) {
            CottRuntime.validateF64(value.value, path: '$path.value');
            return value;
          }
          if (value is JsonString) {
            CottRuntime.validateUnicode(value.value, path: '$path.value');
            return value;
          }
          if (value is JsonArray) {
            for (var index = 0; index < value.value.length; index += 1) {
              state.transform(value.value[index], json, '$path.value[$index]', depth + 1);
            }
            return value;
          }
          if (value is JsonObject) {
            for (final entry in value.value.entries) {
              CottRuntime.validateUnicode(entry.key, path: '$path.key');
              state.transform(entry.value, json, '$path.value[${entry.key}]', depth + 1);
            }
            return value;
          }
          return _mismatch(path, 'JsonValue', value);
        },
      );
}

final class _DeepPair {
  const _DeepPair(this.left, this.right);
  final Object left;
  final Object right;

  @override
  bool operator ==(Object other) =>
      other is _DeepPair && identical(left, other.left) && identical(right, other.right);

  @override
  int get hashCode => Object.hash(identityHashCode(left), identityHashCode(right));
}

final class _DeepComparator {
  final Set<_DeepPair> _active = <_DeepPair>{};
  final Set<_DeepPair> _completed = <_DeepPair>{};
  int _nodes = 0;

  bool equal(Object? left, Object? right, [String path = r'$', int depth = 0]) {
    if (identical(left, right)) return true;
    if (left == null || right == null || left.runtimeType != right.runtimeType) return false;
    if (depth > 64) CottRuntime.violation('$path exceeds equality depth 64', phase: 'validation');
    _nodes += 1;
    if (_nodes > 1024) CottRuntime.violation('$path exceeds equality node limit 1024', phase: 'validation');
    final pair = _DeepPair(left, right);
    if (_completed.contains(pair)) return true;
    if (!_active.add(pair)) {
      CottRuntime.violation('$path contains an active value cycle', phase: 'validation');
    }
    try {
      final result = _equalDirect(left, right, path, depth);
      _active.remove(pair);
      if (result) _completed.add(pair);
      return result;
    } catch (_) {
      _active.remove(pair);
      rethrow;
    }
  }

  bool _equalDirect(Object left, Object right, String path, int depth) {
    if (left is double && right is double) return left == right;
    if (left is CottConst && right is CottConst) return CottRuntime.sameConst(left, right);
    if (left is Opaque || left is Dyn || left is CottTrait || left is CottFactory) return left == right;
    if (left is CottBytes && right is CottBytes) return _sequence(left, right, path, depth);
    if (left is CottBuffer && right is CottBuffer) {
      return CottRuntime.sameConst(left.dimension, right.dimension) && _sequence(left, right, path, depth);
    }
    if (left is CottArray && right is CottArray) {
      return CottRuntime.sameConst(left.dimension, right.dimension) && _sequence(left, right, path, depth);
    }
    if (left is CottTupleValue && right is CottTupleValue) {
      return _sequence(left.cottTupleElements, right.cottTupleElements, path, depth);
    }
    if (left is CottFieldValue && right is CottFieldValue) {
      if (left.cottTypeIdentity != right.cottTypeIdentity ||
          !equal(left.cottFieldNames, right.cottFieldNames, '$path.fields', depth + 1)) {
        return false;
      }
      for (final name in left.cottFieldNames) {
        if (!equal(left.cottField(name), right.cottField(name), '$path.$name', depth + 1)) return false;
      }
      return true;
    }
    if (left is Some && right is Some) return equal(left.value, right.value, '$path.value', depth + 1);
    if (left is Ok && right is Ok) return equal(left.value, right.value, '$path.value', depth + 1);
    if (left is Err && right is Err) return equal(left.error, right.error, '$path.error', depth + 1);
    if (left is JsonArray && right is JsonArray) return _sequence(left.value, right.value, '$path.value', depth);
    if (left is JsonObject && right is JsonObject) return _map(left.value, right.value, '$path.value', depth);
    if (left is List && right is List) return _sequence(left, right, path, depth);
    if (left is Set && right is Set) {
      if (left.length != right.length) return false;
      return left.every((candidate) => right.any((other) => equal(candidate, other, '$path.element', depth + 1)));
    }
    if (left is Map && right is Map) return _map(left, right, path, depth);
    return left == right;
  }

  bool _sequence(Iterable left, Iterable right, String path, int depth) {
    final leftValues = left.toList(growable: false);
    final rightValues = right.toList(growable: false);
    if (leftValues.length != rightValues.length) return false;
    for (var index = 0; index < leftValues.length; index += 1) {
      if (!equal(leftValues[index], rightValues[index], '$path[$index]', depth + 1)) return false;
    }
    return true;
  }

  bool _map(Map left, Map right, String path, int depth) {
    if (left.length != right.length) return false;
    for (final leftEntry in left.entries) {
      var matched = false;
      for (final rightEntry in right.entries) {
        if (equal(leftEntry.key, rightEntry.key, '$path.key', depth + 1) &&
            equal(leftEntry.value, rightEntry.value, '$path[${leftEntry.key}]', depth + 1)) {
          matched = true;
          break;
        }
      }
      if (!matched) return false;
    }
    return true;
  }
}

final class _DeepSnapshotter {
  final Set<Object> _active = HashSet<Object>.identity();
  final Map<Object, Object?> _completed = HashMap<Object, Object?>.identity();
  int _nodes = 0;

  Object? snapshot(Object? value, [String path = r'$', int depth = 0]) {
    if (value == null || value is num || value is BigInt || value is bool || value is String ||
        value is CottConst || value is CottOpaqueTag || value is CottPath || value is Opaque ||
        value is Dyn || value is CottTrait || value is CottFactory || value is CottUnit ||
        value is Nothing || value is JsonNull || value is JsonBoolean || value is JsonInteger ||
        value is JsonFloat || value is JsonString) {
      return value;
    }
    if (depth > 64) CottRuntime.violation('$path exceeds snapshot depth 64', phase: 'validation');
    _nodes += 1;
    if (_nodes > 1024) CottRuntime.violation('$path exceeds snapshot node limit 1024', phase: 'validation');
    if (_completed.containsKey(value)) return _completed[value];
    if (!_active.add(value)) {
      CottRuntime.violation('$path contains an active value cycle', phase: 'validation');
    }
    try {
      final result = _snapshotDirect(value, path, depth);
      _active.remove(value);
      _completed[value] = result;
      return result;
    } catch (_) {
      _active.remove(value);
      rethrow;
    }
  }

  Object? _snapshotDirect(Object value, String path, int depth) {
    if (value is CottBytes) return CottBytes(value);
    if (value is CottBuffer) return CottBuffer<CottConst>(value, value.dimension);
    if (value is CottList) {
      return CottList<Object?>([
        for (var index = 0; index < value.length; index += 1)
          snapshot(value[index], '$path[$index]', depth + 1),
      ]);
    }
    if (value is CottSet) {
      return CottSet<Object?>([
        for (final item in value) snapshot(item, '$path.element', depth + 1),
      ]);
    }
    if (value is CottMap) {
      return CottMap<Object?, Object?>([
        for (final entry in value.entries)
          CottMapEntry(
            snapshot(entry.key, '$path.key', depth + 1),
            snapshot(entry.value, '$path[${entry.key}]', depth + 1),
          ),
      ]);
    }
    if (value is FrozenMap) {
      return FrozenMap<Object?, Object?>.entries([
        for (final entry in value.entries)
          MapEntry(
            snapshot(entry.key, '$path.key', depth + 1),
            snapshot(entry.value, '$path[${entry.key}]', depth + 1),
          ),
      ]);
    }
    if (value is CottKeywordArguments) {
      return CottKeywordArguments<Object?>({
        for (final entry in value.entries)
          entry.key: snapshot(entry.value, '$path[${entry.key}]', depth + 1),
      });
    }
    if (value is CottTupleValue) {
      return value.cottRebuild(CottList([
        for (var index = 0; index < value.cottTupleElements.length; index += 1)
          snapshot(value.cottTupleElements[index], '$path[$index]', depth + 1),
      ]));
    }
    if (value is CottArray) {
      return CottArray<Object?, CottConst>([
        for (var index = 0; index < value.length; index += 1)
          snapshot(value[index], '$path[$index]', depth + 1),
      ], value.dimension);
    }
    if (value is Some) return Some<Object?>(snapshot(value.value, '$path.value', depth + 1));
    if (value is Ok) return Ok<Object?, Object?>(snapshot(value.value, '$path.value', depth + 1));
    if (value is Err) return Err<Object?, Object?>(snapshot(value.error, '$path.error', depth + 1));
    if (value is JsonArray) {
      return JsonArray([
        for (var index = 0; index < value.value.length; index += 1)
          snapshot(value.value[index], '$path.value[$index]', depth + 1) as JsonValue,
      ]);
    }
    if (value is JsonObject) {
      return JsonObject.entries([
        for (final entry in value.value.entries)
          MapEntry(entry.key, snapshot(entry.value, '$path.value[${entry.key}]', depth + 1) as JsonValue),
      ]);
    }
    if (value is List) {
      return List<Object?>.unmodifiable([
        for (var index = 0; index < value.length; index += 1)
          snapshot(value[index], '$path[$index]', depth + 1),
      ]);
    }
    if (value is Set) {
      return Set<Object?>.unmodifiable([
        for (final item in value) snapshot(item, '$path.element', depth + 1),
      ]);
    }
    if (value is Map) {
      return Map<Object?, Object?>.unmodifiable({
        for (final entry in value.entries)
          snapshot(entry.key, '$path.key', depth + 1):
              snapshot(entry.value, '$path[${entry.key}]', depth + 1),
      });
    }
    return value;
  }
}

final class _DeepHasher {
  final Set<Object> _active = HashSet<Object>.identity();
  int _nodes = 0;

  int hash(Object? value, [String path = r'$', int depth = 0]) {
    if (value == null) return 0;
    if (depth > 64) CottRuntime.violation('$path exceeds hash depth 64', phase: 'validation');
    _nodes += 1;
    if (_nodes > 1024) CottRuntime.violation('$path exceeds hash node limit 1024', phase: 'validation');
    if (value is double) return value == 0.0 ? 0.0.hashCode : value.hashCode;
    if (value is CottConst) return Object.hash(value.runtimeType, value.value);
    if (value is num || value is BigInt || value is bool || value is String || value is CottPath ||
        value is Opaque || value is Dyn || value is CottTrait || value is CottFactory ||
        value is CottUnit || value is Nothing || value is JsonNull || value is JsonBoolean ||
        value is JsonInteger || value is JsonFloat || value is JsonString) {
      return value.hashCode;
    }
    if (!_active.add(value)) {
      CottRuntime.violation('$path contains an active value cycle', phase: 'validation');
    }
    try {
      return _hashDirect(value, path, depth);
    } finally {
      _active.remove(value);
    }
  }

  int _ordered(Iterable values, String path, int depth) {
    var result = 1;
    var index = 0;
    for (final value in values) {
      result = _combine(result, hash(value, '$path[$index]', depth + 1));
      index += 1;
    }
    return result;
  }

  int _hashDirect(Object value, String path, int depth) {
    if (value is CottBuffer) return _combine(hash(value.dimension), _ordered(value, path, depth));
    if (value is CottArray) return _combine(hash(value.dimension), _ordered(value, path, depth));
    if (value is CottTupleValue) return _ordered(value.cottTupleElements, path, depth);
    if (value is CottFieldValue) {
      var result = value.cottTypeIdentity.hashCode;
      for (final name in value.cottFieldNames) {
        result = _combine(result, name.hashCode);
        result = _combine(result, hash(value.cottField(name), '$path.$name', depth + 1));
      }
      return result;
    }
    if (value is Some) return hash(value.value, '$path.value', depth + 1);
    if (value is Ok) return hash(value.value, '$path.value', depth + 1);
    if (value is Err) return hash(value.error, '$path.error', depth + 1);
    if (value is JsonArray) return _ordered(value.value, '$path.value', depth);
    if (value is JsonObject) return _map(value.value, '$path.value', depth);
    if (value is List || value is CottList || value is CottBytes) return _ordered(value as Iterable, path, depth);
    if (value is Set) {
      var result = 0;
      for (final item in value) result ^= hash(item, '$path.element', depth + 1);
      return result;
    }
    if (value is Map) return _map(value, path, depth);
    return value.hashCode;
  }

  int _map(Map values, String path, int depth) {
    var result = 0;
    for (final entry in values.entries) {
      result ^= hash(entry.key, '$path.key', depth + 1) ^
          hash(entry.value, '$path[${entry.key}]', depth + 1);
    }
    return result;
  }

  static int _combine(int left, int right) => ((left * 31) + right) & 0x1fffffff;
}

final class CottFixtureKey {
  const CottFixtureKey(this.fixture, this.path);
  final String fixture;
  final String path;

  @override
  bool operator ==(Object other) =>
      other is CottFixtureKey && fixture == other.fixture && path == other.path;

  @override
  int get hashCode => Object.hash(fixture, path);
}

final class CottFixtureContext {
  CottFixtureContext({required this.root, Map<CottFixtureKey, String> urls = const {}})
      : urls = FrozenMap(urls);
  final CottPath root;
  final FrozenMap<CottFixtureKey, String> urls;
}

final class CottRuntime {
  CottRuntime._();

  static const String projectName = cottProjectName;
  static const String projectVersion = cottProjectVersion;
  static const String compilerVersion = cottCompilerVersion;
  static const core.int runtimeAbi = cottRuntimeAbi;

  static final Object _observationKey = Object();
  static final Object _fixturesKey = Object();

  static void requireIdentity(String expectedProjectName, String expectedProjectVersion, core.int expectedAbi) {
    if (expectedProjectName != projectName ||
        expectedProjectVersion != projectVersion ||
        expectedAbi != runtimeAbi) {
      violation(
        'runtime identity mismatch',
        phase: 'identity',
        expected: '$expectedProjectName@$expectedProjectVersion/abi$expectedAbi',
        actual: '$projectName@$projectVersion/abi$runtimeAbi',
      );
    }
  }

  static BigInt int(String decimal) {
    try {
      return BigInt.parse(decimal);
    } on FormatException catch (error, trace) {
      violation(
        'invalid canonical integer',
        phase: 'validation',
        actual: decimal,
        cause: error,
        causeStackTrace: trace,
      );
    }
  }

  static BigInt checkInt(
    BigInt value, {
    required bool signed,
    required core.int bits,
    String path = r'$',
  }) {
    if (bits != 8 && bits != 16 && bits != 32 && bits != 64) {
      violation('invalid integer width', phase: 'validation', actual: '$bits');
    }
    final low = signed ? -(BigInt.one << (bits - 1)) : BigInt.zero;
    final high = signed ? (BigInt.one << (bits - 1)) - BigInt.one : (BigInt.one << bits) - BigInt.one;
    if (value < low || value > high) {
      violation(
        '$path is outside ${signed ? 'signed' : 'unsigned'} $bits-bit range',
        phase: 'validation',
        expected: '$low..$high',
        actual: '$value',
      );
    }
    return value;
  }

  static BigInt mathInt(Object? value) {
    if (value is BigInt) return value;
    if (value is core.int) {
      const maximumExactInt = 0x1fffffffffffff;
      if (value < -maximumExactInt || value > maximumExactInt) {
        return violation(
          'Dart int is outside the portable exact-integer range',
          phase: 'contract-expression',
          expected: '-$maximumExactInt..$maximumExactInt; use BigInt for I64/U64',
          actual: '$value',
        );
      }
      return BigInt.from(value);
    }
    return violation(
      'expected an exact integer',
      phase: 'contract-expression',
      actual: value?.runtimeType.toString() ?? 'null',
    );
  }

  static Object intValue(BigInt value, CottIntKind kind, {String path = r'$'}) {
    final checked = checkInt(value, signed: kind.signed, bits: kind.bits, path: path);
    return kind.usesBigInt ? checked : checked.toInt();
  }

  static core.int i8(String decimal) =>
      intValue(int(decimal), CottIntKind.i8) as core.int;
  static core.int i16(String decimal) =>
      intValue(int(decimal), CottIntKind.i16) as core.int;
  static core.int i32(String decimal) =>
      intValue(int(decimal), CottIntKind.i32) as core.int;
  static BigInt i64(String decimal) =>
      intValue(int(decimal), CottIntKind.i64) as BigInt;
  static core.int u8(String decimal) =>
      intValue(int(decimal), CottIntKind.u8) as core.int;
  static core.int u16(String decimal) =>
      intValue(int(decimal), CottIntKind.u16) as core.int;
  static core.int u32(String decimal) =>
      intValue(int(decimal), CottIntKind.u32) as core.int;
  static BigInt u64(String decimal) =>
      intValue(int(decimal), CottIntKind.u64) as BigInt;

  static Object intAdd(Object? left, Object? right, [CottIntKind? result]) =>
      _integerResult(mathInt(left) + mathInt(right), result);
  static Object intSubtract(Object? left, Object? right, [CottIntKind? result]) =>
      _integerResult(mathInt(left) - mathInt(right), result);
  static Object intMultiply(Object? left, Object? right, [CottIntKind? result]) =>
      _integerResult(mathInt(left) * mathInt(right), result);
  static Object intNegate(Object? value, [CottIntKind? result]) =>
      _integerResult(-mathInt(value), result);

  static Object intDivide(Object? left, Object? right, [CottIntKind? result]) {
    final divisor = mathInt(right);
    if (divisor == BigInt.zero) {
      violation('integer division divisor is zero', phase: 'contract-expression');
    }
    return _integerResult(mathInt(left) ~/ divisor, result);
  }

  static Object euclideanRemainder(Object? left, Object? right, [CottIntKind? result]) {
    final divisor = mathInt(right);
    if (divisor == BigInt.zero) {
      violation('integer remainder divisor is zero', phase: 'contract-expression');
    }
    final magnitude = divisor.abs();
    final remainder = ((mathInt(left) % magnitude) + magnitude) % magnitude;
    return _integerResult(remainder, result);
  }

  static Object euclideanDivide(Object? left, Object? right, [CottIntKind? result]) {
    final dividend = mathInt(left);
    final divisor = mathInt(right);
    if (divisor == BigInt.zero) {
      violation('integer division divisor is zero', phase: 'contract-expression');
    }
    final remainder = euclideanRemainder(dividend, divisor) as BigInt;
    return _integerResult((dividend - remainder) ~/ divisor, result);
  }

  static Object _integerResult(BigInt value, CottIntKind? result) =>
      result == null ? value : intValue(value, result);

  static BigInt constValue<N extends CottConst>(N witness, CottIntKind kind, {String path = r'$'}) {
    if (kind.signed) {
      violation(
        'const generic witness must use an unsigned integer kind',
        phase: 'validation',
        expected: 'U8, U16, U32, or U64',
        actual: kind.name,
      );
    }
    return checkInt(witness.value, signed: false, bits: kind.bits, path: path);
  }

  static N validateConst<N extends CottConst>(N witness, CottIntKind kind, {String path = r'$'}) {
    constValue(witness, kind, path: path);
    return witness;
  }

  static bool sameConst(CottConst left, CottConst right) =>
      left.runtimeType == right.runtimeType && left.value == right.value;

  static core.int constLength(CottConst marker, {String path = r'$'}) {
    const maximum = 0x1fffffffffffff;
    final value = marker.value;
    if (value < BigInt.zero || value > BigInt.from(maximum)) {
      violation(
        '$path is not a portable Dart container length',
        phase: 'validation',
        expected: '0..$maximum',
        actual: '$value',
      );
    }
    return value.toInt();
  }

  static Uint8List bytesFromHex(String hex) {
    if (hex.length.isOdd ||
        !RegExp(r'^[0-9a-fA-F]*$').hasMatch(hex)) {
      violation(
        'invalid canonical hexadecimal bytes',
        phase: 'validation',
        actual: hex,
      );
    }
    return Uint8List.fromList([
      for (var index = 0; index < hex.length; index += 2)
        core.int.parse(hex.substring(index, index + 2), radix: 16),
    ]);
  }

  static double f32FromBits(String bits) {
    if (bits.length != 8) {
      violation(
        'F32 bits must contain exactly 8 hexadecimal digits',
        phase: 'validation',
        actual: bits,
      );
    }
    final data = ByteData.sublistView(bytesFromHex(bits));
    return validateF32(data.getFloat32(0, Endian.big));
  }

  static double f64FromBits(String bits) {
    if (bits.length != 16) {
      violation(
        'F64 bits must contain exactly 16 hexadecimal digits',
        phase: 'validation',
        actual: bits,
      );
    }
    final data = ByteData.sublistView(bytesFromHex(bits));
    return validateF64(data.getFloat64(0, Endian.big));
  }

  static double normalizeF32(double value, {String path = r'$'}) {
    if (!value.isFinite) violation('$path must be a finite F32', phase: 'validation');
    final storage = Float32List(1)..[0] = value;
    final normalized = storage[0];
    if (!normalized.isFinite) violation('$path is outside binary32 range', phase: 'validation');
    return normalized;
  }

  static double validateF32(double value, {String path = r'$'}) => normalizeF32(value, path: path);

  static double validateF64(double value, {String path = r'$'}) {
    if (!value.isFinite) violation('$path must be a finite F64', phase: 'validation');
    return value;
  }

  static double f32Add(double left, double right) => normalizeF32(validateF32(left) + validateF32(right));
  static double f32Subtract(double left, double right) => normalizeF32(validateF32(left) - validateF32(right));
  static double f32Multiply(double left, double right) => normalizeF32(validateF32(left) * validateF32(right));
  static double f32Divide(double left, double right) => normalizeF32(validateF32(left) / validateF32(right));
  static double f32Negate(double value) => normalizeF32(-validateF32(value));
  static double f64Add(double left, double right) => validateF64(validateF64(left) + validateF64(right));
  static double f64Subtract(double left, double right) => validateF64(validateF64(left) - validateF64(right));
  static double f64Multiply(double left, double right) => validateF64(validateF64(left) * validateF64(right));
  static double f64Divide(double left, double right) => validateF64(validateF64(left) / validateF64(right));
  static double f64Negate(double value) => validateF64(-validateF64(value));

  static String validateUnicode(String value, {String path = r'$'}) {
    final units = value.codeUnits;
    var index = 0;
    while (index < units.length) {
      final unit = units[index];
      if (unit >= 0xd800 && unit <= 0xdbff) {
        if (index + 1 >= units.length || units[index + 1] < 0xdc00 || units[index + 1] > 0xdfff) {
          violation('$path contains an unpaired UTF-16 surrogate', phase: 'validation');
        }
        index += 2;
      } else if (unit >= 0xdc00 && unit <= 0xdfff) {
        violation('$path contains an unpaired UTF-16 surrogate', phase: 'validation');
      } else {
        index += 1;
      }
    }
    return value;
  }

  static bool shouldValidate(RuntimeValidation mode) => switch (mode) {
        RuntimeValidation.boundary => true,
        RuntimeValidation.testOnly => Zone.current[_observationKey] is CottObservation,
        RuntimeValidation.off => false,
      };

  static T withTestObservation<T>(CottObservation observation, T Function() body) =>
      runZoned(body, zoneValues: {_observationKey: observation});

  static Future<T> withTestObservationAsync<T>(
    CottObservation observation,
    FutureOr<T> Function() body,
  ) =>
      runZoned(() => Future<T>.sync(body), zoneValues: {_observationKey: observation});

  static T withFixtureContext<T>(CottFixtureContext fixtures, T Function() body) =>
      runZoned(body, zoneValues: {_fixturesKey: fixtures});

  static Future<T> withFixtureContextAsync<T>(
    CottFixtureContext fixtures,
    FutureOr<T> Function() body,
  ) =>
      runZoned(() => Future<T>.sync(body), zoneValues: {_fixturesKey: fixtures});

  static CottFixtureContext _fixtures() {
    final context = Zone.current[_fixturesKey];
    if (context is! CottFixtureContext) {
      violation('fixture access requires an active fixture context', phase: 'fixture');
    }
    return context;
  }

  static CottPath fixturePath(String fixture, String path) {
    validateUnicode(fixture, path: r'$.fixture');
    validateUnicode(path, path: r'$.path');
    if (fixture.isEmpty || path.isEmpty || fixture.contains('/') ||
        path.startsWith('/') || path.split('/').any((part) => part.isEmpty || part == '.' || part == '..')) {
      violation('fixture path is not a safe relative POSIX path', phase: 'fixture');
    }
    return _fixtures().root.join('$fixture/$path');
  }

  static String fixtureUrl(String fixture, String path) {
    final context = _fixtures();
    final result = context.urls[CottFixtureKey(fixture, path)];
    if (result == null) {
      violation(
        'fixture URL route is not configured',
        phase: 'fixture',
        expected: '$fixture:$path',
      );
    }
    final uri = Uri.tryParse(result);
    if (uri == null ||
        (uri.scheme != 'http' && uri.scheme != 'https') ||
        !(uri.host == 'localhost' || uri.host == '127.0.0.1' || uri.host == '::1') ||
        uri.userInfo.isNotEmpty) {
      violation('fixture URL must be loopback HTTP without user information', phase: 'fixture');
    }
    return result;
  }

  static T abi<T>(
    Object? value,
    CottType<T> type, {
    RuntimeValidation mode = RuntimeValidation.boundary,
    String path = r'$',
  }) =>
      _Traversal(!shouldValidate(mode)).transform(value, type, path, 0);

  static T returnValue<T>(
    Object? value,
    CottType<T> type, {
    RuntimeValidation mode = RuntimeValidation.boundary,
    String path = r'$.return',
  }) {
    final validated = abi(value, type, mode: mode, path: path);
    return _Adaptation().transform(
      validated,
      type as CottType<Object?>,
      mode,
      path,
      0,
    ) as T;
  }

  static bool canonicalEqual(Object? left, Object? right) {
    if (identical(left, right)) return true;
    if ((left is core.int || left is BigInt) && (right is core.int || right is BigInt)) {
      return mathInt(left) == mathInt(right);
    }
    if (left is CottConst && right is CottConst) return sameConst(left, right);
    if (left == null || right == null || left.runtimeType != right.runtimeType) return false;
    if (left is String || left is bool || left is num || left is BigInt || left is CottPath || left is Type) {
      return left == right;
    }
    return _DeepComparator().equal(left, right);
  }

  static core.int canonicalCompare(Object? left, Object? right) {
    if ((left is core.int || left is BigInt) && (right is core.int || right is BigInt)) {
      return mathInt(left).compareTo(mathInt(right));
    }
    if (left == null || right == null || left.runtimeType != right.runtimeType) {
      return violation(
        'canonical ordering requires compatible exact types',
        phase: 'contract-expression',
        expected: left?.runtimeType.toString() ?? 'null',
        actual: right?.runtimeType.toString() ?? 'null',
      );
    }
    if (left is String && right is String) {
      validateUnicode(left);
      validateUnicode(right);
      final leftRunes = left.runes.iterator;
      final rightRunes = right.runes.iterator;
      while (true) {
        final hasLeft = leftRunes.moveNext();
        final hasRight = rightRunes.moveNext();
        if (!hasLeft || !hasRight) return hasLeft == hasRight ? 0 : (hasLeft ? 1 : -1);
        final compared = leftRunes.current.compareTo(rightRunes.current);
        if (compared != 0) return compared;
      }
    }
    if (left is double && right is double) {
      validateF64(left);
      validateF64(right);
      return left.compareTo(right);
    }
    if (left is num && right is num) return left.compareTo(right);
    if (left is Comparable<Object?>) {
      try {
        return left.compareTo(right);
      } catch (error, trace) {
        return violation(
          'value has no canonical ordering',
          phase: 'contract-expression',
          cause: error,
          causeStackTrace: trace,
        );
      }
    }
    return violation('value has no canonical ordering', phase: 'contract-expression');
  }

  static bool startsWith(Object? value, Object? prefix) =>
      value is String && prefix is String && value.startsWith(prefix);
  static bool endsWith(Object? value, Object? suffix) =>
      value is String && suffix is String && value.endsWith(suffix);

  static bool contains(Object? value, Object? member) {
    if (value is String) return member is String && value.contains(member);
    if (value is CottTupleValue) {
      return value.cottTupleElements.any((item) => canonicalEqual(item, member));
    }
    if (value is Iterable) return value.any((item) => canonicalEqual(item, member));
    if (value is Map) return value.keys.any((item) => canonicalEqual(item, member));
    return false;
  }

  static BigInt length(Object? value) {
    if (value is String) {
      validateUnicode(value);
      return BigInt.from(value.runes.length);
    }
    if (value is CottTupleValue) return BigInt.from(value.cottTupleElements.length);
    if (value is Iterable) return BigInt.from(value.length);
    if (value is Map) return BigInt.from(value.length);
    return violation('len operand has no canonical length', phase: 'contract-expression');
  }

  static Object? _selected(Object? value, Object selector, String? fieldName) {
    if (selector is Object? Function(Object?)) return selector(value);
    if (selector is String) return field(value, selector, fieldName);
    return violation('invalid field selector', phase: 'contract-expression');
  }

  static bool uniqueBy(Iterable<Object?> values, Object selector, [String? fieldName]) {
    final seen = <Object?>[];
    for (final value in values) {
      final selected = _selected(value, selector, fieldName);
      if (seen.any((prior) => canonicalEqual(prior, selected))) return false;
      seen.add(selected);
    }
    return true;
  }

  static bool descendingBy(Iterable<Object?> values, Object selector, [String? fieldName]) {
    final iterator = values.iterator;
    if (!iterator.moveNext()) return true;
    var previous = _selected(iterator.current, selector, fieldName);
    while (iterator.moveNext()) {
      final current = _selected(iterator.current, selector, fieldName);
      if (canonicalCompare(current, previous) > 0) return false;
      previous = current;
    }
    return true;
  }

  static Object? field(Object? value, String ownerOrName, [String? name]) {
    if (value is! CottFieldValue) {
      return violation(
        'value does not expose canonical field',
        phase: 'contract-expression',
        expected: name ?? ownerOrName,
        actual: value?.runtimeType.toString() ?? 'null',
      );
    }
    final fieldName = name ?? ownerOrName;
    if (name != null && value.cottTypeIdentity != ownerOrName) {
      return violation(
        'field owner identity mismatch',
        phase: 'contract-expression',
        expected: ownerOrName,
        actual: value.cottTypeIdentity,
      );
    }
    if (fieldName.isEmpty || !value.cottFieldNames.contains(fieldName)) {
      return violation(
        'value does not expose canonical field',
        phase: 'contract-expression',
        expected: fieldName,
        actual: value.cottTypeIdentity,
      );
    }
    return value.cottField(fieldName);
  }

  static CottOption<Object?> resultOk(Object? value) =>
      value is Ok ? Some<Object?>(value.value) : const Nothing<Object?>();
  static CottOption<Object?> resultErr(Object? value) =>
      value is Err ? Some<Object?>(value.error) : const Nothing<Object?>();
  static Object? resultError(Object? value) => value is Err ? value.error : null;
  static CottOption<Object?> optionSome(Object? value) =>
      value is Some ? Some<Object?>(value.value) : const Nothing<Object?>();
  static CottOption<CottList<Object?>> variant(Object? value, String expectedVariant) =>
      value is CottVariant && value.cottVariant == expectedVariant
          ? Some<CottList<Object?>>(value.cottPayload)
          : const Nothing<CottList<Object?>>();
  static bool matchesResultOk(Object? value) => value is Ok;
  static bool matchesResultErr(Object? value) => value is Err;
  static bool matchesSome(Object? value) => value is Some;
  static bool matchesNothing(Object? value) => value is Nothing;
  static bool matchesVariant(Object? value, String expectedVariant) =>
      value is CottVariant && value.cottVariant == expectedVariant;

  static Object? deepSnapshot(Object? value) => _DeepSnapshotter().snapshot(value);
  static bool deepEqual(Object? left, Object? right) => _DeepComparator().equal(left, right);
  static core.int deepHash(Object? value) => _DeepHasher().hash(value);

  static void _observe(bool condition, String symbol, String phase, String? clause) {
    final observation = Zone.current[_observationKey];
    if (observation is CottObservation && clause != null) {
      observation._record(CottClauseObservation(
        symbol: symbol,
        clause: clause,
        phase: phase,
        status: condition ? CottObservationStatus.passed : CottObservationStatus.failed,
      ));
    }
  }

  static void recordUnobserved(
    String symbol,
    String phase,
    String clause,
    String reason,
  ) {
    final observation = Zone.current[_observationKey];
    if (observation is CottObservation) {
      observation._record(CottClauseObservation(
        symbol: symbol,
        clause: clause,
        phase: phase,
        status: CottObservationStatus.unobserved,
        reason: reason,
      ));
    }
  }

  static void checkContract(
    bool condition,
    String symbol,
    String phase, {
    String? clause,
    CottSpan? span,
    String? expected,
    String? actual,
  }) {
    _observe(condition, symbol, phase, clause);
    if (!condition) {
      violation(
        '$phase clause failed',
        symbol: symbol,
        phase: phase,
        clause: clause,
        span: span,
        expected: expected,
        actual: actual,
      );
    }
  }

  static void requireContract(
    bool condition,
    String symbol, {
    String? clause,
    CottSpan? span,
    String? expected,
    String? actual,
  }) =>
      checkContract(
        condition,
        symbol,
        'requires',
        clause: clause,
        span: span,
        expected: expected,
        actual: actual,
      );

  static void ensureContract(
    bool condition,
    String symbol, {
    String? clause,
    CottSpan? span,
    String? expected,
    String? actual,
  }) =>
      checkContract(
        condition,
        symbol,
        'ensures',
        clause: clause,
        span: span,
        expected: expected,
        actual: actual,
      );

  static void invariant(
    bool condition,
    String symbol, {
    String? clause,
    CottSpan? span,
    String? expected,
    String? actual,
  }) =>
      checkContract(
        condition,
        symbol,
        'invariant',
        clause: clause,
        span: span,
        expected: expected,
        actual: actual,
      );

  static void requireEffect(
    bool allowed,
    String effect,
    String symbol, {
    CottSpan? span,
  }) {
    if (!allowed) {
      violation(
        'effect is not enabled',
        symbol: symbol,
        phase: 'effect',
        span: span,
        expected: effect,
        actual: 'disabled',
      );
    }
  }

  static CottBytes snapshotBytes(Iterable<core.int> bytes) => CottBytes(bytes);
  static CottBuffer<N> snapshotBuffer<N extends CottConst>(Iterable<core.int> bytes, N dimension) =>
      CottBuffer(bytes, dimension);
  static CottList<T> snapshotList<T>(Iterable<T> values) => CottList(values);
  static CottSet<T> snapshotSet<T>(Iterable<T> values) => CottSet(values);
  static CottMap<K, V> snapshotMap<K, V>(Map<K, V> values) => CottMap.fromMap(values);
  static CottTuple snapshotTuple(Iterable<Object?> values) => CottTuple(values);
  static CottArray<T, N> snapshotArray<T, N extends CottConst>(Iterable<T> values, N dimension) =>
      CottArray(values, dimension);

  static CottIterator<T> wrapIterator<T>(
    CottIteratorSource<T> source,
    CottType<T> item, {
    RuntimeValidation mode = RuntimeValidation.boundary,
    String path = r'$.return',
  }) =>
      CottIterator(source, item, mode: mode, path: path);

  static CottGenerator<Y, S, R> wrapGenerator<Y, S, R>(
    CottGeneratorSource<Y, S, R> source,
    CottType<Y> yielded,
    CottType<S> sent,
    CottType<R> returned, {
    RuntimeValidation mode = RuntimeValidation.boundary,
    String path = r'$.return',
  }) =>
      CottGenerator(source, yielded, sent, returned, mode: mode, path: path);

  static CottAsyncIterator<T> wrapAsyncIterator<T>(
    CottAsyncIteratorSource<T> source,
    CottType<T> item, {
    RuntimeValidation mode = RuntimeValidation.boundary,
    String path = r'$.return',
  }) =>
      CottAsyncIterator(source, item, mode: mode, path: path);

  static CottAsyncGenerator<Y, S, R> wrapAsyncGenerator<Y, S, R>(
    CottAsyncGeneratorSource<Y, S, R> source,
    CottType<Y> yielded,
    CottType<S> sent,
    CottType<R> returned, {
    RuntimeValidation mode = RuntimeValidation.boundary,
    String path = r'$.return',
  }) =>
      CottAsyncGenerator(source, yielded, sent, returned, mode: mode, path: path);

  static Never rethrowImplementation(
    Object error,
    StackTrace stackTrace,
    String symbol, {
    CottSpan? span,
    bool asynchronous = false,
  }) {
    if (error is CottContractViolation) {
      error.symbol ??= symbol;
      error.span ??= span;
      Error.throwWithStackTrace(error, stackTrace);
    }
    if (asynchronous && error is CottCancellationException) {
      Error.throwWithStackTrace(error, stackTrace);
    }
    if (error is Error) Error.throwWithStackTrace(error, stackTrace);
    return violation(
      'implementation raised an undeclared exception',
      symbol: symbol,
      phase: 'implementation-call',
      span: span,
      expected: 'declared Result error or ordinary return',
      actual: error.runtimeType.toString(),
      cause: error,
      causeStackTrace: stackTrace,
    );
  }

  static String encodeTaggedJson(JsonValue value) => jsonEncode(_jsonWire(value));

  static Object? _jsonWire(JsonValue value) => switch (value) {
        JsonNull() => <String, Object?>{r'$cott': 'null'},
        JsonBoolean(:final value) => <String, Object?>{r'$cott': 'boolean', 'value': value},
        JsonInteger(:final value) => <String, Object?>{r'$cott': 'integer', 'value': '$value'},
        JsonFloat(:final value) => <String, Object?>{r'$cott': 'float', 'value': value},
        JsonString(:final value) => <String, Object?>{r'$cott': 'string', 'value': value},
        JsonArray(:final value) => <String, Object?>{
            r'$cott': 'array',
            'value': [for (final item in value) _jsonWire(item)],
          },
        JsonObject(:final value) => <String, Object?>{
            r'$cott': 'object',
            'value': <String, Object?>{
              for (final entry in value.entries) entry.key: _jsonWire(entry.value),
            },
          },
      };

  static JsonValue decodeTaggedJson(String source) {
    validateUnicode(source);
    return _jsonFromWire(jsonDecode(source), r'$');
  }

  static JsonValue _jsonFromWire(Object? wire, String path) {
    if (wire is! Map || wire[r'$cott'] is! String) {
      return violation('$path is not tagged Cott JSON', phase: 'validation');
    }
    final tag = wire[r'$cott'];
    final allowed = tag == 'null' ? <Object>{r'$cott'} : <Object>{r'$cott', 'value'};
    if (wire.keys.length != allowed.length || wire.keys.any((key) => !allowed.contains(key))) {
      return violation('$path has invalid tagged JSON members', phase: 'validation');
    }
    final value = wire['value'];
    return switch (tag) {
      'null' => const JsonNull(),
      'boolean' when value is bool => JsonBoolean(value),
      'integer' when value is String => JsonInteger(int(value)),
      'float' when value is double => JsonFloat(value),
      'string' when value is String => JsonString(value),
      'array' when value is List => JsonArray([
          for (var index = 0; index < value.length; index += 1)
            _jsonFromWire(value[index], '$path.value[$index]'),
        ]),
      'object' when value is Map => JsonObject.entries([
          for (final entry in value.entries)
            if (entry.key is String)
              MapEntry(entry.key as String, _jsonFromWire(entry.value, '$path.value[${entry.key}]'))
            else
              violation('$path.value has a non-string key', phase: 'validation'),
        ]),
      _ => violation('$path has an invalid tagged JSON payload', phase: 'validation', actual: '$tag'),
    };
  }

  static Never violation(
    String detail, {
    String? symbol,
    String? phase,
    CottSpan? span,
    String? expected,
    String? actual,
    String? clause,
    Object? cause,
    StackTrace? causeStackTrace,
  }) =>
      throw CottContractViolation(
        detail,
        symbol: symbol,
        phase: phase,
        span: span,
        expected: expected,
        actual: actual,
        clause: clause,
        cause: cause,
        causeStackTrace: causeStackTrace,
      );
}

sealed class CottStep<T> {
  const CottStep();
}

final class CottYield<T> extends CottStep<T> {
  const CottYield(this.value);
  final T value;
}

final class CottDone<T> extends CottStep<T> {
  const CottDone();
}

sealed class CottGeneratorStep<Y, R> {
  const CottGeneratorStep();
}

final class CottGeneratorYield<Y, R> extends CottGeneratorStep<Y, R> {
  const CottGeneratorYield(this.value);
  final Y value;
}

final class CottGeneratorReturn<Y, R> extends CottGeneratorStep<Y, R> {
  const CottGeneratorReturn(this.value);
  final R value;
}

abstract interface class CottIteratorSource<T> {
  factory CottIteratorSource.callbacks({
    required CottStep<T> Function() next,
    required void Function() close,
  }) = _CottIteratorCallbacks<T>;

  CottStep<T> next();
  void close();
}

abstract interface class CottGeneratorSource<Y, S, R> {
  factory CottGeneratorSource.callbacks({
    required CottGeneratorStep<Y, R> Function() start,
    required CottGeneratorStep<Y, R> Function() next,
    required CottGeneratorStep<Y, R> Function(S value) send,
    required CottGeneratorStep<Y, R> Function(
      Object error,
      StackTrace stackTrace,
    ) raise,
    required void Function() close,
  }) = _CottGeneratorCallbacks<Y, S, R>;

  CottGeneratorStep<Y, R> start();
  CottGeneratorStep<Y, R> next();
  CottGeneratorStep<Y, R> send(S value);
  CottGeneratorStep<Y, R> raise(Object error, StackTrace stackTrace);
  void close();
}

abstract interface class CottAsyncIteratorSource<T> {
  factory CottAsyncIteratorSource.callbacks({
    required FutureOr<CottStep<T>> Function(
      CottCancellationToken? cancellation,
    ) next,
    required FutureOr<void> Function(
      CottCancellationToken? cancellation,
    ) close,
  }) = _CottAsyncIteratorCallbacks<T>;

  Future<CottStep<T>> next({CottCancellationToken? cancellation});
  Future<void> close({CottCancellationToken? cancellation});
}

abstract interface class CottAsyncGeneratorSource<Y, S, R> {
  factory CottAsyncGeneratorSource.callbacks({
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      CottCancellationToken? cancellation,
    ) start,
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      CottCancellationToken? cancellation,
    ) next,
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      S value,
      CottCancellationToken? cancellation,
    ) send,
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      Object error,
      StackTrace stackTrace,
      CottCancellationToken? cancellation,
    ) raise,
    required FutureOr<void> Function(
      CottCancellationToken? cancellation,
    ) close,
  }) = _CottAsyncGeneratorCallbacks<Y, S, R>;

  Future<CottGeneratorStep<Y, R>> start({CottCancellationToken? cancellation});
  Future<CottGeneratorStep<Y, R>> next({CottCancellationToken? cancellation});
  Future<CottGeneratorStep<Y, R>> send(S value, {CottCancellationToken? cancellation});
  Future<CottGeneratorStep<Y, R>> raise(
    Object error,
    StackTrace stackTrace, {
    CottCancellationToken? cancellation,
  });
  Future<void> close({CottCancellationToken? cancellation});
}

final class _CottIteratorCallbacks<T> implements CottIteratorSource<T> {
  _CottIteratorCallbacks({
    required CottStep<T> Function() next,
    required void Function() close,
  })  : _next = next,
        _close = close;
  final CottStep<T> Function() _next;
  final void Function() _close;
  @override
  CottStep<T> next() => _next();
  @override
  void close() => _close();
}

final class _CottGeneratorCallbacks<Y, S, R>
    implements CottGeneratorSource<Y, S, R> {
  _CottGeneratorCallbacks({
    required CottGeneratorStep<Y, R> Function() start,
    required CottGeneratorStep<Y, R> Function() next,
    required CottGeneratorStep<Y, R> Function(S value) send,
    required CottGeneratorStep<Y, R> Function(
      Object error,
      StackTrace stackTrace,
    ) raise,
    required void Function() close,
  })  : _start = start,
        _next = next,
        _send = send,
        _raise = raise,
        _close = close;
  final CottGeneratorStep<Y, R> Function() _start;
  final CottGeneratorStep<Y, R> Function() _next;
  final CottGeneratorStep<Y, R> Function(S value) _send;
  final CottGeneratorStep<Y, R> Function(
    Object error,
    StackTrace stackTrace,
  ) _raise;
  final void Function() _close;
  @override
  CottGeneratorStep<Y, R> start() => _start();
  @override
  CottGeneratorStep<Y, R> next() => _next();
  @override
  CottGeneratorStep<Y, R> send(S value) => _send(value);
  @override
  CottGeneratorStep<Y, R> raise(
    Object error,
    StackTrace stackTrace,
  ) =>
      _raise(error, stackTrace);
  @override
  void close() => _close();
}

final class _CottAsyncIteratorCallbacks<T>
    implements CottAsyncIteratorSource<T> {
  _CottAsyncIteratorCallbacks({
    required FutureOr<CottStep<T>> Function(
      CottCancellationToken? cancellation,
    ) next,
    required FutureOr<void> Function(
      CottCancellationToken? cancellation,
    ) close,
  })  : _next = next,
        _close = close;

  final FutureOr<CottStep<T>> Function(
    CottCancellationToken? cancellation,
  ) _next;
  final FutureOr<void> Function(CottCancellationToken? cancellation) _close;

  @override
  Future<CottStep<T>> next({CottCancellationToken? cancellation}) =>
      Future<CottStep<T>>.sync(() => _next(cancellation));

  @override
  Future<void> close({CottCancellationToken? cancellation}) =>
      Future<void>.sync(() => _close(cancellation));
}

final class _CottAsyncGeneratorCallbacks<Y, S, R>
    implements CottAsyncGeneratorSource<Y, S, R> {
  _CottAsyncGeneratorCallbacks({
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      CottCancellationToken? cancellation,
    ) start,
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      CottCancellationToken? cancellation,
    ) next,
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      S value,
      CottCancellationToken? cancellation,
    ) send,
    required FutureOr<CottGeneratorStep<Y, R>> Function(
      Object error,
      StackTrace stackTrace,
      CottCancellationToken? cancellation,
    ) raise,
    required FutureOr<void> Function(
      CottCancellationToken? cancellation,
    ) close,
  })  : _start = start,
        _next = next,
        _send = send,
        _raise = raise,
        _close = close;

  final FutureOr<CottGeneratorStep<Y, R>> Function(
    CottCancellationToken? cancellation,
  ) _start;
  final FutureOr<CottGeneratorStep<Y, R>> Function(
    CottCancellationToken? cancellation,
  ) _next;
  final FutureOr<CottGeneratorStep<Y, R>> Function(
    S value,
    CottCancellationToken? cancellation,
  ) _send;
  final FutureOr<CottGeneratorStep<Y, R>> Function(
    Object error,
    StackTrace stackTrace,
    CottCancellationToken? cancellation,
  ) _raise;
  final FutureOr<void> Function(CottCancellationToken? cancellation) _close;

  @override
  Future<CottGeneratorStep<Y, R>> start({
    CottCancellationToken? cancellation,
  }) =>
      Future<CottGeneratorStep<Y, R>>.sync(() => _start(cancellation));

  @override
  Future<CottGeneratorStep<Y, R>> next({
    CottCancellationToken? cancellation,
  }) =>
      Future<CottGeneratorStep<Y, R>>.sync(() => _next(cancellation));

  @override
  Future<CottGeneratorStep<Y, R>> send(
    S value, {
    CottCancellationToken? cancellation,
  }) =>
      Future<CottGeneratorStep<Y, R>>.sync(
        () => _send(value, cancellation),
      );

  @override
  Future<CottGeneratorStep<Y, R>> raise(
    Object error,
    StackTrace stackTrace, {
    CottCancellationToken? cancellation,
  }) =>
      Future<CottGeneratorStep<Y, R>>.sync(
        () => _raise(error, stackTrace, cancellation),
      );

  @override
  Future<void> close({CottCancellationToken? cancellation}) =>
      Future<void>.sync(() => _close(cancellation));
}

enum _ProtocolState { newValue, active, done, closed }

final class _OperationGuard {
  _OperationGuard(this.phase);
  final String phase;
  bool _active = false;

  T run<T>(T Function() body) {
    _begin();
    try {
      return body();
    } finally {
      _active = false;
    }
  }

  Future<T> runAsync<T>(FutureOr<T> Function() body) async {
    _begin();
    try {
      return await body();
    } finally {
      _active = false;
    }
  }

  void _begin() {
    if (_active) {
      CottRuntime.violation('concurrent protocol operation', phase: phase);
    }
    _active = true;
  }
}

final class CottIterator<T> implements Iterator<T> {
  CottIterator(
    this._source,
    this._item, {
    this.mode = RuntimeValidation.boundary,
    this.path = r'$.return',
  });

  final CottIteratorSource<T> _source;
  final CottType<T> _item;
  final RuntimeValidation mode;
  final String path;
  final _OperationGuard _guard = _OperationGuard('iterator-lifecycle');
  _ProtocolState _state = _ProtocolState.newValue;
  T? _current;

  bool _matches(CottType<Object?> item, RuntimeValidation expectedMode) =>
      identical(_item, item) && mode == expectedMode;

  @override
  T get current => _current as T;

  @override
  bool moveNext() => _guard.run(() {
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) return false;
        final step = _source.next();
        switch (step) {
          case CottDone<T>():
            _state = _ProtocolState.done;
            _current = null;
            return false;
          case CottYield<T>(:final value):
            _state = _ProtocolState.active;
            _current = CottRuntime.returnValue(value, _item, mode: mode, path: '$path.yield');
            return true;
        }
      });

  void close() => _guard.run(() {
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) return;
        _source.close();
        _state = _ProtocolState.closed;
        _current = null;
      });
}

final class CottGenerator<Y, S, R> implements Iterator<Y> {
  CottGenerator(
    this._source,
    this._yielded,
    this._sent,
    this._returned, {
    this.mode = RuntimeValidation.boundary,
    this.path = r'$.return',
  });

  final CottGeneratorSource<Y, S, R> _source;
  final CottType<Y> _yielded;
  final CottType<S> _sent;
  final CottType<R> _returned;
  final RuntimeValidation mode;
  final String path;
  final _OperationGuard _guard = _OperationGuard('generator-lifecycle');
  _ProtocolState _state = _ProtocolState.newValue;
  CottOption<R> _completion = const Nothing<Never>();
  Y? _current;

  bool _matches(
    CottType<Object?> yielded,
    CottType<Object?> sent,
    CottType<Object?> returned,
    RuntimeValidation expectedMode,
  ) =>
      identical(_yielded, yielded) &&
      identical(_sent, sent) &&
      identical(_returned, returned) &&
      mode == expectedMode;

  CottGeneratorStep<Y, R> _validate(CottGeneratorStep<Y, R> step) {
    switch (step) {
      case CottGeneratorYield<Y, R>(:final value):
        _state = _ProtocolState.active;
        return CottGeneratorYield(
          CottRuntime.returnValue(value, _yielded, mode: mode, path: '$path.yield'),
        );
      case CottGeneratorReturn<Y, R>(:final value):
        final result = CottRuntime.returnValue(value, _returned, mode: mode, path: '$path.return');
        _completion = Some(result);
        _state = _ProtocolState.done;
        return CottGeneratorReturn(result);
    }
  }

  CottGeneratorStep<Y, R> _advance() {
    if (_state == _ProtocolState.done) {
      return CottGeneratorReturn((_completion as Some<R>).value);
    }
    if (_state == _ProtocolState.closed) {
      return CottRuntime.violation('generator is closed', phase: 'generator-lifecycle');
    }
    return _validate(
      _state == _ProtocolState.newValue ? _source.start() : _source.next(),
    );
  }

  CottGeneratorStep<Y, R> nextStep() => _guard.run(_advance);

  CottGeneratorStep<Y, R> send(S value) => _guard.run(() {
        if (_state == _ProtocolState.newValue) {
          CottRuntime.violation('generator must be started before send', phase: 'generator-lifecycle');
        }
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) {
          CottRuntime.violation('generator is complete', phase: 'generator-lifecycle');
        }
        return _validate(_source.send(CottRuntime.abi(value, _sent, mode: mode, path: '$path.send')));
      });

  CottGeneratorStep<Y, R> throwInto(Object error, StackTrace stackTrace) => _guard.run(() {
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) {
          CottRuntime.violation('generator is complete', phase: 'generator-lifecycle');
        }
        return _validate(_source.raise(error, stackTrace));
      });

  CottOption<R> get returnValue => _completion;

  @override
  Y get current => _current as Y;

  @override
  bool moveNext() => _guard.run(() {
        final step = _advance();
        switch (step) {
          case CottGeneratorYield<Y, R>(:final value):
            _current = value;
            return true;
          case CottGeneratorReturn<Y, R>():
            _current = null;
            return false;
        }
      });

  void close() => _guard.run(() {
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) return;
        _source.close();
        _state = _ProtocolState.closed;
        _current = null;
      });
}

final class CottAsyncIterator<T> {
  CottAsyncIterator(
    this._source,
    this._item, {
    this.mode = RuntimeValidation.boundary,
    this.path = r'$.return',
  });

  final CottAsyncIteratorSource<T> _source;
  final CottType<T> _item;
  final RuntimeValidation mode;
  final String path;
  final _OperationGuard _guard = _OperationGuard('async-lifecycle');
  _ProtocolState _state = _ProtocolState.newValue;

  bool _matches(CottType<Object?> item, RuntimeValidation expectedMode) =>
      identical(_item, item) && mode == expectedMode;

  Future<CottStep<T>> next({CottCancellationToken? cancellation}) => _guard.runAsync(() async {
        cancellation?.throwIfCancelled();
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) return const CottDone<Never>();
        final step = await _source.next(cancellation: cancellation);
        cancellation?.throwIfCancelled();
        switch (step) {
          case CottDone<T>():
            _state = _ProtocolState.done;
            return const CottDone<Never>();
          case CottYield<T>(:final value):
            _state = _ProtocolState.active;
            return CottYield(CottRuntime.returnValue(value, _item, mode: mode, path: '$path.yield'));
        }
      });

  Future<void> close({CottCancellationToken? cancellation}) => _guard.runAsync(() async {
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) return;
        cancellation?.throwIfCancelled();
        await _source.close(cancellation: cancellation);
        _state = _ProtocolState.closed;
      });
}

final class CottAsyncGenerator<Y, S, R> {
  CottAsyncGenerator(
    this._source,
    this._yielded,
    this._sent,
    this._returned, {
    this.mode = RuntimeValidation.boundary,
    this.path = r'$.return',
  });

  final CottAsyncGeneratorSource<Y, S, R> _source;
  final CottType<Y> _yielded;
  final CottType<S> _sent;
  final CottType<R> _returned;
  final RuntimeValidation mode;
  final String path;
  final _OperationGuard _guard = _OperationGuard('async-lifecycle');
  _ProtocolState _state = _ProtocolState.newValue;
  CottOption<R> _completion = const Nothing<Never>();

  bool _matches(
    CottType<Object?> yielded,
    CottType<Object?> sent,
    CottType<Object?> returned,
    RuntimeValidation expectedMode,
  ) =>
      identical(_yielded, yielded) &&
      identical(_sent, sent) &&
      identical(_returned, returned) &&
      mode == expectedMode;

  CottGeneratorStep<Y, R> _validate(CottGeneratorStep<Y, R> step) {
    switch (step) {
      case CottGeneratorYield<Y, R>(:final value):
        _state = _ProtocolState.active;
        return CottGeneratorYield(
          CottRuntime.returnValue(value, _yielded, mode: mode, path: '$path.yield'),
        );
      case CottGeneratorReturn<Y, R>(:final value):
        final result = CottRuntime.returnValue(value, _returned, mode: mode, path: '$path.return');
        _completion = Some(result);
        _state = _ProtocolState.done;
        return CottGeneratorReturn(result);
    }
  }

  Future<CottGeneratorStep<Y, R>> start({CottCancellationToken? cancellation}) =>
      _guard.runAsync(() async {
        if (_state != _ProtocolState.newValue) {
          CottRuntime.violation('async generator has already started', phase: 'async-lifecycle');
        }
        cancellation?.throwIfCancelled();
        final step = await _source.start(cancellation: cancellation);
        cancellation?.throwIfCancelled();
        return _validate(step);
      });

  Future<CottGeneratorStep<Y, R>> next({CottCancellationToken? cancellation}) =>
      _guard.runAsync(() async {
        cancellation?.throwIfCancelled();
        if (_state == _ProtocolState.done) {
          return CottGeneratorReturn((_completion as Some<R>).value);
        }
        if (_state == _ProtocolState.closed) {
          return CottRuntime.violation('async generator is closed', phase: 'async-lifecycle');
        }
        final step = _state == _ProtocolState.newValue
            ? await _source.start(cancellation: cancellation)
            : await _source.next(cancellation: cancellation);
        cancellation?.throwIfCancelled();
        return _validate(step);
      });

  Future<CottGeneratorStep<Y, R>> send(
    S value, {
    CottCancellationToken? cancellation,
  }) =>
      _guard.runAsync(() async {
        if (_state == _ProtocolState.newValue) {
          CottRuntime.violation('async generator must be started before send', phase: 'async-lifecycle');
        }
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) {
          CottRuntime.violation('async generator is complete', phase: 'async-lifecycle');
        }
        cancellation?.throwIfCancelled();
        final checked = CottRuntime.abi(value, _sent, mode: mode, path: '$path.send');
        final step = await _source.send(checked, cancellation: cancellation);
        cancellation?.throwIfCancelled();
        return _validate(step);
      });

  Future<CottGeneratorStep<Y, R>> throwInto(
    Object error,
    StackTrace stackTrace, {
    CottCancellationToken? cancellation,
  }) =>
      _guard.runAsync(() async {
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) {
          CottRuntime.violation('async generator is complete', phase: 'async-lifecycle');
        }
        cancellation?.throwIfCancelled();
        final step = await _source.raise(error, stackTrace, cancellation: cancellation);
        cancellation?.throwIfCancelled();
        return _validate(step);
      });

  CottOption<R> get returnValue => _completion;

  Future<void> close({CottCancellationToken? cancellation}) => _guard.runAsync(() async {
        if (_state == _ProtocolState.done || _state == _ProtocolState.closed) return;
        cancellation?.throwIfCancelled();
        await _source.close(cancellation: cancellation);
        _state = _ProtocolState.closed;
      });
}

final class CottCancellationToken {
  CottCancellationToken._(this._cancelled);
  final Completer<Object?> _cancelled;

  bool get isCancelled => _cancelled.isCompleted;
  Object? get reason => isCancelled ? _reason : null;
  Object? _reason;
  Future<Object?> get whenCancelled => _cancelled.future;

  void throwIfCancelled() {
    if (isCancelled) throw CottCancellationException(_reason);
  }
}

final class CottCancellationSource {
  CottCancellationSource({CottCancellationToken? parent})
      : _cancelled = Completer<Object?>() {
    token = CottCancellationToken._(_cancelled);
    if (parent != null) {
      if (parent.isCancelled) {
        cancel(parent.reason);
      } else {
        parent.whenCancelled.then(cancel);
      }
    }
  }

  final Completer<Object?> _cancelled;
  late final CottCancellationToken token;

  void cancel([Object? reason = 'cancelled']) {
    if (_cancelled.isCompleted) return;
    token._reason = reason;
    _cancelled.complete(reason);
  }
}

final class CottTask<T> {
  CottTask._(this.result, this._source);
  final Future<T> result;
  final CottCancellationSource _source;
  void cancel([Object? reason = 'task cancelled']) => _source.cancel(reason);
}

final class _TaskFailure {
  const _TaskFailure(this.error, this.stackTrace);
  final Object error;
  final StackTrace stackTrace;
}

final class CottTaskScope {
  CottTaskScope({CottCancellationToken? parent}) : _source = CottCancellationSource(parent: parent);

  final CottCancellationSource _source;
  final List<Future<void>> _owned = <Future<void>>[];
  final List<_TaskFailure> _failures = <_TaskFailure>[];
  bool _closed = false;

  CottCancellationToken get cancellation => _source.token;

  CottTask<T> spawn<T>(FutureOr<T> Function(CottCancellationToken) operation) {
    if (_closed) {
      CottRuntime.violation('task scope is closed', phase: 'task-lifecycle');
    }
    final child = CottCancellationSource(parent: cancellation);
    final result = Future<T>.sync(() {
      child.token.throwIfCancelled();
      return operation(child.token);
    });
    final observed = result.then<void>(
      (_) {},
      onError: (Object error, StackTrace trace) {
        _failures.add(_TaskFailure(error, trace));
      },
    );
    _owned.add(observed);
    return CottTask._(result, child);
  }

  void cancel([Object? reason = 'task scope cancelled']) => _source.cancel(reason);

  Future<void> join() async {
    final snapshot = List<Future<void>>.of(_owned);
    await Future.wait(snapshot);
    if (_failures.isNotEmpty) {
      final failure = _failures.first;
      Error.throwWithStackTrace(failure.error, failure.stackTrace);
    }
  }

  Future<void> close({bool cancelOwned = false}) async {
    if (_closed) return;
    _closed = true;
    if (cancelOwned) cancel('task scope closed');
    await join();
  }

  static Future<T> run<T>(
    FutureOr<T> Function(CottTaskScope) body, {
    CottCancellationToken? parent,
  }) async {
    final scope = CottTaskScope(parent: parent);
    try {
      final result = await body(scope);
      await scope.close();
      return result;
    } catch (error, trace) {
      scope.cancel(error);
      try {
        await scope.close();
      } catch (_) {
        // The body failure remains primary; child failures are still observed.
      }
      Error.throwWithStackTrace(error, trace);
    }
  }
}

final class CottGuardLease {
  CottGuardLease._(this._guard);
  final CottResourceGuard _guard;
  bool _active = true;
  bool _nestedActive = false;
}

final class _GuardWaiter {
  _GuardWaiter(this.completer, this.cancellation);
  final Completer<CottGuardLease> completer;
  final CottCancellationToken? cancellation;
  bool queued = true;
}

final class CottResourceGuard {
  bool _locked = false;
  final Queue<_GuardWaiter> _waiters = Queue<_GuardWaiter>();

  T runSync<T>(T Function(CottGuardLease) action) {
    if (_locked) {
      CottRuntime.violation(
        'resource guard is held by an asynchronous or unrelated operation',
        phase: 'resource-lifecycle',
      );
    }
    _locked = true;
    final lease = CottGuardLease._(this);
    try {
      return action(lease);
    } finally {
      _release(lease);
    }
  }

  Future<T> runExclusive<T>(
    FutureOr<T> Function(CottGuardLease) action, {
    CottCancellationToken? cancellation,
  }) async {
    cancellation?.throwIfCancelled();
    final lease = await _acquire(cancellation);
    try {
      cancellation?.throwIfCancelled();
      return await action(lease);
    } finally {
      _release(lease);
    }
  }

  T withLease<T>(CottGuardLease lease, T Function() action) {
    _verifyLease(lease);
    if (lease._nestedActive) {
      CottRuntime.violation('concurrent use of resource guard lease', phase: 'resource-lifecycle');
    }
    lease._nestedActive = true;
    try {
      return action();
    } finally {
      lease._nestedActive = false;
    }
  }

  Future<T> withLeaseAsync<T>(
    CottGuardLease lease,
    FutureOr<T> Function() action, {
    CottCancellationToken? cancellation,
  }) async {
    _verifyLease(lease);
    if (lease._nestedActive) {
      CottRuntime.violation('concurrent use of resource guard lease', phase: 'resource-lifecycle');
    }
    cancellation?.throwIfCancelled();
    lease._nestedActive = true;
    try {
      final result = await action();
      cancellation?.throwIfCancelled();
      return result;
    } finally {
      lease._nestedActive = false;
    }
  }

  Future<CottGuardLease> _acquire(CottCancellationToken? cancellation) {
    if (!_locked && _waiters.isEmpty) {
      _locked = true;
      return Future.value(CottGuardLease._(this));
    }
    final completer = Completer<CottGuardLease>();
    final waiter = _GuardWaiter(completer, cancellation);
    _waiters.addLast(waiter);
    if (cancellation != null) {
      cancellation.whenCancelled.then((reason) {
        if (!waiter.queued) return;
        if (_waiters.remove(waiter)) {
          waiter.queued = false;
          completer.completeError(CottCancellationException(reason), StackTrace.current);
        }
      });
    }
    return completer.future;
  }

  void _verifyLease(CottGuardLease lease) {
    if (!identical(lease._guard, this) || !lease._active || !_locked) {
      CottRuntime.violation('invalid or expired resource guard lease', phase: 'resource-lifecycle');
    }
  }

  void _release(CottGuardLease lease) {
    _verifyLease(lease);
    lease._active = false;
    while (_waiters.isNotEmpty) {
      final waiter = _waiters.removeFirst();
      waiter.queued = false;
      if (waiter.cancellation?.isCancelled ?? false) {
        if (!waiter.completer.isCompleted) {
          waiter.completer.completeError(
            CottCancellationException(waiter.cancellation!.reason),
            StackTrace.current,
          );
        }
        continue;
      }
      final next = CottGuardLease._(this);
      waiter.completer.complete(next);
      return;
    }
    _locked = false;
  }
}

final class CottStateField {
  const CottStateField({
    required this.name,
    required this.type,
    required this.read,
    required this.write,
  });
  final String name;
  final CottType<Object?> type;
  final Object? Function() read;
  final void Function(Object?) write;
}

final class CottTransition {
  const CottTransition({required this.field, required this.from, required this.to});
  final String field;
  final Object from;
  final Object to;
}

final class CottInvariant {
  const CottInvariant({required this.clause, required this.check, this.span})
      : _checked = null;
  CottInvariant.checked({
    required this.clause,
    required void Function() check,
    this.span,
  })  : _checked = check,
        check = (() { check(); return true; });
  final void Function()? _checked;
  final String clause;
  final bool Function() check;
  final CottSpan? span;
}

final class CottStateSnapshot {
  CottStateSnapshot._(this.values);
  final FrozenMap<String, Object?> values;
}

final class CottStateMutation {
  CottStateMutation._(this._contract, this._lease);
  final CottResourceContract _contract;
  final CottGuardLease _lease;
  bool _active = true;

  /// Compiler-generated wrappers use this only to forward explicit ownership
  /// to a nested resource wrapper. Authored bindings are not allowed to name it.
  CottGuardLease get compilerLease {
    _contract._verifyMutation(this);
    return _lease;
  }

  Object? read(String field) {
    _contract._verifyMutation(this);
    return _contract._field(field).read();
  }

  void write(String field, Object? value) {
    _contract._verifyMutation(this);
    if (!_contract._writableField(field)) {
      CottRuntime.violation(
        'state mutation is outside the declared frame',
        symbol: _contract.symbol,
        phase: 'modifies',
        actual: field,
      );
    }
    final stateField = _contract._field(field);
    final checked = CottRuntime.abi(
      value,
      stateField.type,
      path: '\$.${stateField.name}',
    );
    stateField.write(checked);
  }

  void _revoke() => _active = false;
}

final class CottResourceContract {
  CottResourceContract({
    required this.symbol,
    required Iterable<CottStateField> fields,
    required Iterable<String> modifies,
    required Iterable<CottTransition> transitions,
    required Iterable<CottInvariant> invariants,
    CottResourceGuard? guard,
  })  : fields = CottList(fields),
        modifies = CottSet(modifies),
        transitions = CottList(transitions),
        invariants = CottList(invariants),
        guard = guard ?? CottResourceGuard() {
    final names = this.fields.map((field) => field.name).toList(growable: false);
    if (names.any((name) => name.isEmpty) || names.toSet().length != names.length) {
      CottRuntime.violation('resource state fields must be unique and non-empty', symbol: symbol, phase: 'state');
    }
    final known = names.toSet();
    if (this.modifies.any((name) => !known.contains(name)) ||
        this.transitions.any((transition) => !known.contains(transition.field))) {
      CottRuntime.violation('resource rules reference an unknown state field', symbol: symbol, phase: 'state');
    }
  }

  final String symbol;
  final CottList<CottStateField> fields;
  final CottSet<String> modifies;
  final CottList<CottTransition> transitions;
  final CottList<CottInvariant> invariants;
  final CottResourceGuard guard;

  CottStateSnapshot snapshot() => CottStateSnapshot._(FrozenMap({
        for (final field in fields) field.name: CottRuntime.deepSnapshot(field.read()),
      }));

  CottStateField _field(String name) {
    for (final field in fields) {
      if (field.name == name) return field;
    }
    return CottRuntime.violation(
      'state mutation references an unknown field',
      symbol: symbol,
      phase: 'state',
      actual: name,
    );
  }

  bool _writableField(String name) =>
      modifies.contains(name) ||
      transitions.any((transition) => transition.field == name);

  void _verifyMutation(CottStateMutation mutation) {
    if (!identical(mutation._contract, this) || !mutation._active) {
      CottRuntime.violation(
        'invalid or revoked state mutation capability',
        symbol: symbol,
        phase: 'resource-lifecycle',
      );
    }
    guard._verifyLease(mutation._lease);
  }

  void _validateState() {
    for (final field in fields) {
      final raw = field.read();
      final validated = CottRuntime.abi(raw, field.type, path: '\$.${field.name}');
      if (!CottRuntime.deepEqual(raw, validated)) field.write(validated);
    }
  }

  void _validateTransitions(CottStateSnapshot old, bool exceptional) {
    for (final transition in transitions) {
      final before = old.values[transition.field];
      final stateField = fields.firstWhere((field) => field.name == transition.field);
      final after = stateField.read();
      if (!identical(before, transition.from)) {
        CottRuntime.violation(
          exceptional ? 'exceptional resource transition source failed' : 'resource transition source failed',
          symbol: symbol,
          phase: exceptional ? 'exceptional-transitions' : 'transitions',
          expected: '${transition.field} identity ${transition.from}',
          actual: '$before',
        );
      }
      final targetMatches = identical(after, transition.to);
      if ((!exceptional && !targetMatches) ||
          (exceptional && !identical(after, before) && !targetMatches)) {
        CottRuntime.violation(
          exceptional ? 'exceptional resource transition target failed' : 'resource transition target failed',
          symbol: symbol,
          phase: exceptional ? 'exceptional-transitions' : 'transitions',
          expected: exceptional ? 'old or ${transition.to}' : '${transition.to}',
          actual: '$after',
        );
      }
    }
  }

  void _validateFrame(CottStateSnapshot old, bool exceptional) {
    final transitionFields = transitions.map((transition) => transition.field).toSet();
    for (final field in fields) {
      if (!modifies.contains(field.name) &&
          !transitionFields.contains(field.name) &&
          !CottRuntime.deepEqual(field.read(), old.values[field.name])) {
        CottRuntime.violation(
          'resource frame changed an unpermitted field',
          symbol: symbol,
          phase: exceptional ? 'exceptional-modifies' : 'modifies',
          expected: '${field.name} unchanged',
          actual: '${field.name} changed',
        );
      }
    }
  }

  void _validateInvariants() {
    for (final invariant in invariants) {
      final checked = invariant._checked;
      if (checked != null) {
        checked();
        continue;
      }
      CottRuntime.invariant(
        invariant.check(),
        symbol,
        clause: invariant.clause,
        span: invariant.span,
        expected: invariant.clause,
        actual: 'false',
      );
    }
  }

  void validateInitial() {
    _validateState();
    _validateInvariants();
  }

  void validateNormal(CottStateSnapshot old) {
    _validateState();
    _validateTransitions(old, false);
    _validateFrame(old, false);
    _validateInvariants();
  }

  void validateExceptional(CottStateSnapshot old) {
    _validateState();
    _validateTransitions(old, true);
    _validateFrame(old, true);
    _validateInvariants();
  }

  T enforceMutation<R, T>(
    void Function(CottStateMutation) before,
    R Function(CottStateMutation, CottGuardLease) implementation,
    T Function(R, CottStateMutation) after, {
    CottGuardLease? lease,
  }) {
    T execute(CottGuardLease activeLease) {
      final mutation = CottStateMutation._(this, activeLease);
      try {
        final old = snapshot();
        before(mutation);
        late R raw;
        try {
          raw = implementation(mutation, activeLease);
        } catch (_) {
          validateExceptional(old);
          rethrow;
        }
        validateNormal(old);
        return after(raw, mutation);
      } finally {
        mutation._revoke();
      }
    }

    return lease == null
        ? guard.runSync(execute)
        : guard.withLease(lease, () => execute(lease));
  }

  Future<T> enforceMutationAsync<R, T>(
    FutureOr<void> Function(CottStateMutation) before,
    FutureOr<R> Function(CottStateMutation, CottGuardLease) implementation,
    FutureOr<T> Function(R, CottStateMutation) after, {
    CottGuardLease? lease,
    CottCancellationToken? cancellation,
  }) async {
    Future<T> execute(CottGuardLease activeLease) async {
      final mutation = CottStateMutation._(this, activeLease);
      try {
        final old = snapshot();
        await before(mutation);
        late R raw;
        try {
          raw = await implementation(mutation, activeLease);
        } catch (_) {
          validateExceptional(old);
          rethrow;
        }
        validateNormal(old);
        return await after(raw, mutation);
      } finally {
        mutation._revoke();
      }
    }

    if (lease != null) {
      return guard.withLeaseAsync(
        lease,
        () => execute(lease),
        cancellation: cancellation,
      );
    }
    return guard.runExclusive(execute, cancellation: cancellation);
  }

  T withMutation<T>(
    T Function(CottStateMutation) body, {
    CottGuardLease? lease,
  }) =>
      enforceMutation<void, T>(
        (_) {},
        (_, __) {},
        (_, mutation) => body(mutation),
        lease: lease,
      );

  Future<T> withMutationAsync<T>(
    FutureOr<T> Function(CottStateMutation) body, {
    CottGuardLease? lease,
    CottCancellationToken? cancellation,
  }) =>
      enforceMutationAsync<void, T>(
        (_) {},
        (_, __) {},
        (_, mutation) => body(mutation),
        lease: lease,
        cancellation: cancellation,
      );
}
"####;

fn dart_string_literal(value: &str) -> String {
    let mut escaped = String::with_capacity(value.len() + 2);
    escaped.push('\'');
    for character in value.chars() {
        match character {
            '\\' => escaped.push_str("\\\\"),
            '\'' => escaped.push_str("\\'"),
            '$' => escaped.push_str("\\$"),
            '\n' => escaped.push_str("\\n"),
            '\r' => escaped.push_str("\\r"),
            '\t' => escaped.push_str("\\t"),
            '\u{0008}' => escaped.push_str("\\b"),
            '\u{000C}' => escaped.push_str("\\f"),
            character if character.is_control() => {
                use std::fmt::Write as _;
                write!(escaped, "\\u{{{:x}}}", character as u32)
                    .expect("writing to String cannot fail");
            }
            character => escaped.push(character),
        }
    }
    escaped.push('\'');
    escaped
}

fn substitute_runtime_markers(replacements: &[(&str, String)]) -> String {
    let mut rendered = String::with_capacity(RUNTIME_TEMPLATE.len() + 64);
    let mut remaining = RUNTIME_TEMPLATE;
    loop {
        let next = replacements
            .iter()
            .enumerate()
            .filter_map(|(index, (marker, _))| remaining.find(marker).map(|offset| (offset, index)))
            .min_by_key(|(offset, _)| *offset);
        let Some((offset, index)) = next else {
            rendered.push_str(remaining);
            return rendered;
        };
        let (marker, replacement) = &replacements[index];
        rendered.push_str(&remaining[..offset]);
        rendered.push_str(replacement);
        remaining = &remaining[offset + marker.len()..];
    }
}

/// Render the compiler-owned, stdlib-only Dart runtime package files.
pub fn render_runtime(project_name: &str, project_version: &str) -> BTreeMap<PathBuf, Vec<u8>> {
    let source = substitute_runtime_markers(&[
        (
            "__COTT_PROJECT_NAME_LITERAL__",
            dart_string_literal(project_name),
        ),
        (
            "__COTT_PROJECT_VERSION_LITERAL__",
            dart_string_literal(project_version),
        ),
        (
            "__COTT_RUNTIME_VERSION_LITERAL__",
            dart_string_literal(env!("CARGO_PKG_VERSION")),
        ),
    ]);
    BTreeMap::from([(
        PathBuf::from("dart/lib/cott_runtime.dart"),
        source.into_bytes(),
    )])
}
