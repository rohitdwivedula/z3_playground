from z3 import *
import argparse
import time

def calculate_shares(arr):
    shares = []
    N = len(arr)
    for i in range(N):
        if i == 0:
            left = 0
            right = (arr[0] + arr[1]) / 2
        elif i == N - 1:
            left = (arr[N - 2] + arr[N - 1]) / 2
            right = 1
        else:
            left = (arr[i - 1] + arr[i]) / 2
            right = (arr[i] + arr[i + 1]) / 2
        shares.append(right - left)
    return shares

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--N", default=2, type=int)
    parser.add_argument("--max-sols", default=100, type=int)
    parser.add_argument("--verbose", action='store_true', default=False)
    args = parser.parse_args()

    N = args.N
    assert N >= 2, "atleast 2 players needed"

    start_time = time.time()
    s = Solver()
    # N positions
    x = [Real(f'x{i}') for i in range(N)]
    for i in range(len(x)):
        s.add(x[i] >= 0, x[i] <= 1)
        if i > 0:
            s.add(x[i] >= x[i-1])


    og_shares = calculate_shares(x)

    for i in range(N):
        # there is no way for the i-th person to unilaterally change their position
        # while others stay fixed and increase their profit
        
        new_list = x[:i] + x[i+1:]
        M = len(new_list)

        if args.verbose:
            print(f"Playing as player={i}")
            print(f"\tnew_list: {new_list}")
        
        # now within this new list we will try to divide into subcases: what if this i^th person
        # were to be placed between (j-1)^th person and j^th person on the list (let's call this xij_alt). 
        for j in range(M+1):
            if args.verbose:
                print(f"\t\tWhat if I was between {j-1} and {j} idx in new_list?")
            
            x_ij = Real(f'x{i}{j}_alt')
            
            if j == 0:
                range_constraint = And(x_ij >= 0, x_ij <= new_list[j])
            elif j == M:
                range_constraint = And(x_ij >= new_list[j-1], x_ij <= 1)
            else:
                range_constraint = And(x_ij >= new_list[j-1], x_ij <= new_list[j])
            if args.verbose:
                print(f"\t\t\t{range_constraint}")

            alternate_reality = new_list[:j] + [x_ij] + new_list[j:]
            alternate_reality_shares = calculate_shares(alternate_reality)
            
            s.add(ForAll(x_ij, Implies(range_constraint, alternate_reality_shares[j] <= og_shares[i]) ))
            if args.verbose:
                print(f"\t\t\t{s.assertions()[-1]}")
    models = []
    i = 0
    while s.check() == sat:
        m = s.model()
        models.append([m.evaluate(xi) for xi in x])
        print(f"Solution {i+1}:", models[-1])
        i += 1
        if len(models) >= args.max_sols:
            print("EARLY EXITING")
            end_time = time.time()        
            print(f"Took: {round(end_time - start_time, 2)}s")
            return    
        s.add(Or([xi != m.evaluate(xi) for xi in x]))
    
    end_time = time.time()        
    print(f"Took: {round(end_time - start_time, 2)}s")
    
    print("No equilibrium found.")
            

if __name__ == "__main__":
    main()