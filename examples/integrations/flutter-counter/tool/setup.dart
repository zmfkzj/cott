import 'dart:io';

Future<void> main(List<String> arguments) async {
  if (arguments.isNotEmpty) {
    stderr.writeln('usage: dart tool/setup.dart');
    exitCode = 64;
    return;
  }

  final project = File.fromUri(Platform.script).parent.parent.absolute;
  final flutter = Directory(_join(project.path, 'flutter'));
  final deployment = _join(flutter.path, 'cott_module');

  if (!File(_join(project.path, 'cott.toml')).isFileSync() ||
      !File(_join(flutter.path, 'pubspec.yaml')).isFileSync()) {
    stderr.writeln(
      'setup must run from the checked-in Flutter counter example',
    );
    exitCode = 1;
    return;
  }
  if (FileSystemEntity.typeSync(deployment, followLinks: false) !=
      FileSystemEntityType.notFound) {
    stderr.writeln(
      'refusing to overwrite flutter/cott_module; remove the prior trusted '
      'deployment explicitly before rerunning setup',
    );
    exitCode = 1;
    return;
  }

  final cott = Platform.environment['COTT_BIN'] ?? 'cott';
  final flutterCommand = Platform.environment['FLUTTER_BIN'] ?? 'flutter';
  try {
    await _run(cott, ['emit', 'dart', '--project', project.path], project.path);
    await _run(cott, ['verify', '--project', project.path], project.path);
    await _run(cott, [
      'deploy',
      '--project',
      project.path,
      '--output',
      'flutter/cott_module',
    ], project.path);
    if (!File(_join(deployment, 'pubspec.yaml')).isFileSync()) {
      throw StateError('Cott deployment did not produce a Dart package');
    }
    await _run(flutterCommand, ['pub', 'get'], flutter.path);
  } on Object catch (error) {
    stderr.writeln('setup failed: $error');
    exitCode = 1;
  }
}

Future<void> _run(
  String executable,
  List<String> arguments,
  String workingDirectory,
) async {
  stdout.writeln(running(executable, arguments));
  final process = await Process.start(
    executable,
    arguments,
    workingDirectory: workingDirectory,
    mode: ProcessStartMode.inheritStdio,
  );
  final status = await process.exitCode;
  if (status != 0) {
    throw ProcessException(
      executable,
      arguments,
      'command exited with status $status',
      status,
    );
  }
}

String running(String executable, List<String> arguments) =>
    ([executable, ...arguments].map(_shellWord).join(' '));

String _shellWord(String value) => value.contains(RegExp(r"[\s'\\]"))
    ? "'${value.replaceAll("'", "'\\''")}'"
    : value;

String _join(String parent, String child) =>
    '$parent${Platform.pathSeparator}$child';

extension on File {
  bool isFileSync() =>
      FileSystemEntity.typeSync(path, followLinks: false) ==
      FileSystemEntityType.file;
}
