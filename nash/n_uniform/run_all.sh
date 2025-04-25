#!/bin/bash

mkdir -p outputs

for N in $(seq 2 100); do
    timestamp=$(date +"%Y%m%d_%H%M%S")
    outfile="outputs/N${N}_${timestamp}.txt"
    echo "Running N=$N..."
    timeout 20m python3 n_player_uniform.py --N "$N" > "$outfile"
    echo "Logged to $outfile"
done
