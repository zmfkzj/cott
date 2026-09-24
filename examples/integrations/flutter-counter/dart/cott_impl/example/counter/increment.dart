int _cott_example_counter_increment(int current) {
  if (current < 0 || current >= 100) {
    throw ArgumentError.value(current, 'current', 'must satisfy 0 <= current < 100');
  }
  return current + 1;
}
