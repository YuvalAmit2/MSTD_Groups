#!/bin/bash
# Repeatedly run one subdivision generation for 60 seconds, preserve completed
# leaves, cancel the tail, and split each unfinished leaf another 256 ways.
#SBATCH --job-name=bd-k30-rec-controller
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=128M
#SBATCH --time=04:00:00
#SBATCH --output=log/recursive_controller_%j.log

set -euo pipefail
HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
STATE="$HERE/recursive_state"
cd "$HERE"

gen=3
parent_n=1310720000

while :; do
    parents="$STATE/parents_gen${gen}.txt"
    count=$(wc -l < "$parents")
    if ((count == 0)); then
        echo "No unfinished leaves at generation $gen"
        break
    fi
    if ((parent_n > 72057594037927935)); then
        echo "Cannot multiply modulus $parent_n by 256 without uint64 overflow" >&2
        exit 2
    fi
    new_n=$((parent_n * 256))
    total=$((count * 256))
    elements=$(((total + 15) / 16))
    outdir="$HERE/out_k30_recursive/gen_${gen}"
    mkdir -p "$outdir"
    echo "$(date): generation=$gen parents=$count children=$total modulus=$new_n elements=$elements"

    job=$(PARENTS_FILE="$parents" PARENT_N="$parent_n" GEN="$gen" \
        sbatch --parsable --partition=scavenger-aarch64 --account=scavenger \
        --qos=scavenger-aarch64 --nodelist='oasis[00-12,14-36,38]' \
        --array="0-$((elements-1))%${elements}" --time=03:30:00 --requeue \
        --export=ALL,PARENTS_FILE="$parents",PARENT_N="$parent_n",GEN="$gen" \
        slurm_k30_recursive_worker.sh)
    echo "Submitted generation $gen as $job"
    sleep 60
    scancel "$job" 2>/dev/null || true
    while squeue -h -j "$job" 2>/dev/null | grep -q .; do sleep 1; done

    next="$STATE/parents_gen$((gen+1)).txt"
    : > "$next"
    while read -r parent; do
        for ((q=0; q<256; q++)); do
            child=$((parent + q * parent_n))
            file="$outdir/task_${child}.txt"
            if [[ ! -s "$file" ]] || ! grep -q "task ${child}/${new_n}" "$file"; then
                echo "$child" >> "$next"
            fi
        done
    done < "$parents"
    remaining=$(wc -l < "$next")
    echo "$(date): generation=$gen complete=$((total-remaining))/$total remaining=$remaining"
    if ((remaining == 0)); then break; fi
    parent_n=$new_n
    gen=$((gen + 1))
done

python3 combine_k30_recursive.py "$HERE"
