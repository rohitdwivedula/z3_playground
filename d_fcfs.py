from z3 import *
import argparse
import time

def extract(model, var_list):
    return [model[v].as_long() for v in var_list]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_cpus", default=3, type=int)
    parser.add_argument("--n_requests", default=15, type=int)
    parser.add_argument("--total_duration", default=10, type=int, help="Last request arrives on or before")
    parser.add_argument(
        "--req_distribution", 
        choices=["uniform", "bimodal"], 
        default="bimodal", 
        help="Request service time distribution"
    )
    args = parser.parse_args()

    queue       = [Int(f'q_{i}') for i in range(args.n_requests)]
    arrival     = [Int(f'arr_{i}') for i in range(args.n_requests)] # timestamp the request arrived
    service     = [Int(f'serv_{i}') for i in range(args.n_requests)] # time taken to process request
    finish_time = [Int(f'finish_{i}') for i in range(args.n_requests)] # timestamp the request finish

    s = Solver()

    # - each request must be placed in one of N queues;
    # - arrival must be in bounds, and in non-decreasing order
    for i in range(args.n_requests):
        s.add(queue[i] >= 0, queue[i] < args.n_cpus)
        s.add(arrival[i] >= 0, arrival[i] < args.total_duration)
        if i+1 < args.n_requests:
            s.add(arrival[i] <= arrival[i+1])

    # - rate limit of max (2*n_requests)/total_duration at every timestep
    rate_limit = (2 * args.n_requests) // args.total_duration    
    for t in range(args.total_duration):
        s.add(Sum([If(arrival[i] == t, 1, 0) for i in range(args.n_requests)]) <= rate_limit)

    if args.req_distribution == "uniform":
        for i in range(args.n_requests):
            s.add(service[i] == 1)

    elif args.req_distribution == "bimodal":
        # Bimodal distribution where:
        #       - requests take either 'a' cycles or 'b' cycles (b > a)
        #       - probability of a request being an 'a' type request = p
        a = 1
        b = 5
        p = 10.0/11.0 # type 'a' 10x likelier than type 'b'

        for i in range(args.n_requests):
            s.add(Or(service[i] == a, service[i] == b))
        
        # let Z = service[i]
        # Var[Z] = E[Z^2] - (E[Z])^2
        # 95% bounds for this: E[Z] +/- 2*std(Z)
        e_z = (p*a) + ((1-p)*b)
        e_z2 = (p*a*a) + ((1-p) * b * b)
        var_z = e_z2 - (e_z * e_z)
        std_Z = var_z ** 0.5

        lower_bound = e_z - 2 * (std_Z)
        upper_bound = e_z + 2 * (std_Z)
        
        print(f"[bimodal] Setting constraint of sum b/w [{max(lower_bound, a)}, {upper_bound}] ")
        if lower_bound > a:
            s.add(Sum(service) >= args.n_requests * lower_bound)
        s.add(Sum(service) <= args.n_requests * upper_bound)
    else:
        raise NotImplementedError(f"{args.req_distribution} not supported")

    # ensure that new jobs can start only after previous jobs finished
    for i in range(args.n_requests):
        start_time = arrival[i]
        for j in range(i):
            start_time = If(
                And(queue[i] == queue[j], finish_time[j] > start_time), 
                finish_time[j], 
                start_time
            )
        s.add(finish_time[i] == start_time + service[i])
    
    for i in range(args.n_requests):
        pending_jobs = []
        for cpu in range(args.n_cpus):
            jobs_in_queue = []
            for j in range(i):
                jobs_in_queue.append(If(And(queue[j] == cpu, finish_time[j] > arrival[i]), 1, 0))
            pending_jobs.append(Sum(jobs_in_queue))


        for cpu in range(args.n_cpus):
            s.add(Implies(
                queue[i] == cpu,
                And([
                    pending_jobs[cpu] <= pending_jobs[other]
                    for other in range(args.n_cpus) if other != cpu
                ])
            ))


    # Enforce at least one request has wait time > exec time
    some_wait_more_than_exec = [
        finish_time[i] - arrival[i] - service[i] > service[i]
        for i in range(args.n_requests)
    ]
    s.add(Or(some_wait_more_than_exec))
    
    start = time.time()
    s.check()
    end = time.time()

    print(f"[z3] n_constraints={len(s.assertions())}, time={round(end-start, 2)}s")

    model = s.model()

    print("[arrivals]", extract(model, arrival))
    print("[service_times]", extract(model, service))
    print("[cpu_executed_on]", extract(model, queue))
    print("[finish_time]", extract(model, finish_time))

if __name__ == "__main__":
    main()