import 'package:flutter/material.dart';
import 'package:flutter_counter/modules/example/counter.dart';

const int _minimumCount = 0;
const int _maximumCount = 100;

void main() {
  runApp(const CounterApp());
}

class CounterApp extends StatelessWidget {
  const CounterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      restorationScopeId: 'counter_app',
      title: 'Cott Counter',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      home: const CounterPage(),
    );
  }
}

class CounterPage extends StatefulWidget {
  const CounterPage({super.key});

  @override
  State<CounterPage> createState() => _CounterPageState();
}

class _CounterPageState extends State<CounterPage> with RestorationMixin {
  final RestorableInt _count = RestorableInt(_minimumCount);

  @override
  String? get restorationId => 'counter_page';

  @override
  void restoreState(RestorationBucket? oldBucket, bool initialRestore) {
    registerForRestoration(_count, 'count');
    if (_count.value < _minimumCount || _count.value > _maximumCount) {
      _count.value = _minimumCount;
    }
  }

  @override
  void dispose() {
    _count.dispose();
    super.dispose();
  }

  void _incrementCount() {
    if (_count.value >= _maximumCount) {
      return;
    }
    setState(() {
      _count.value = increment(_count.value);
    });
  }

  void _decrementCount() {
    if (_count.value <= _minimumCount) {
      return;
    }
    setState(() {
      _count.value = decrement(_count.value);
    });
  }

  @override
  Widget build(BuildContext context) {
    final count = _count.value;
    return Scaffold(
      appBar: AppBar(title: const Text('Cott Counter')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Counter value'),
            Text(
              '$count',
              key: const ValueKey('counter-value'),
              style: Theme.of(context).textTheme.displayLarge,
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                FilledButton.tonalIcon(
                  key: const ValueKey('decrement-button'),
                  onPressed: count > _minimumCount ? _decrementCount : null,
                  icon: const Icon(Icons.remove),
                  label: const Text('Decrement'),
                ),
                const SizedBox(width: 16),
                FilledButton.icon(
                  key: const ValueKey('increment-button'),
                  onPressed: count < _maximumCount ? _incrementCount : null,
                  icon: const Icon(Icons.add),
                  label: const Text('Increment'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
