from z3 import *

s = Solver()

# Positions of the two players
x1 = Real('x1')
x2 = Real('x2')
s.add(x1 >= 0, x1 <= 1)
s.add(x2 >= 0, x2 <= 1)
s.add(x1 <= x2)

# How much customer mass each player gets:
# Player 1 gets from 0 to (x1 + x2)/2
# Player 2 gets from (x1 + x2)/2 to 1

x1_share = (x1 + x2) / 2
x2_share = 1 - (x1 + x2) / 2

# Alternative positions
x1_alt = Real('x1_alt')
x2_alt = Real('x2_alt')
s.add(x1_alt >= 0, x1_alt <= 1)
s.add(x2_alt >= 0, x2_alt <= 1)

x1_share_alt = If(x1_alt <= x2, (x1_alt + x2) / 2, 1 - (x1_alt + x2) / 2)
s.add(ForAll(x1_alt, x1_share_alt <= x1_share ))

x2_share_alt = If(x2_alt <= x1, (x2_alt + x1) / 2, 1 - (x2_alt + x1) / 2)
s.add(ForAll(x2_alt, x2_share_alt <= x2_share ))

if s.check() == sat:
    m = s.model()
    print("Player 1 position:", m[x1])
    print("Player 2 position:", m[x2])
else:
    print("No equilibrium found.")