int _cott_example_counter_decrement(int current) {
  if (current <= 0 || current > 100) {
    throw ArgumentError.value(current, 'current', 'must be in 1..100');
  }
  return current - 1;
}
