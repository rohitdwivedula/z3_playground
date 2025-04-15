from z3 import *
import random

memory_size = 100
cache_size = 4
all_objects = [Int(f"obj_{i}") for i in range(memory_size)]
cache = [Int(f'cache_{i}') for i in range(cache_size)]

s = Solver()

# Assume all current cache items are unique
s.add(Distinct(*cache))
for i in range(cache_size):
    s.add(cache[i] >= 0)
    s.add(cache[i] < memory_size)
s.check()

print(s.model())