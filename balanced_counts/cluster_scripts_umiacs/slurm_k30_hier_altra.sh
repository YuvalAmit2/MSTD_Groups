#!/bin/bash
# Split the 12 atomic depth-6 branches at depth 18, 256 ways each.
#SBATCH --job-name=bd-k30-hier
#SBATCH --array=0-191
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=256M
#SBATCH --output=log/hier_%A_%a.log

set -euo pipefail
HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE"

mapfile -t parents < recursive_state/parents_gen7.txt
parent_n=5629499534213120000
child_n=256
total=$((${#parents[@]} * child_n))
outdir=out_k30_hier
mkdir -p "$outdir"

run_lane() {
    local lane=$1 linear pi child parent out tmp
    linear=$((SLURM_ARRAY_TASK_ID * SLURM_CPUS_PER_TASK + lane))
    ((linear < total)) || return 0
    pi=$((linear / child_n))
    child=$((linear % child_n))
    parent=${parents[$pi]}
    out="$outdir/parent_${parent}_child_${child}.txt"
    if [[ -s "$out" ]] && grep -q "task ${child}/${child_n}" "$out"; then return 0; fi
    tmp="${out}.tmp.${SLURM_ARRAY_JOB_ID}.${SLURM_ARRAY_TASK_ID}.${lane}"
    ./balanced_dihedral_arm64 30 "$child_n" "$child" 18 \
        "$parent_n" "$parent" 6 > "$tmp"
    mv "$tmp" "$out"
}

pids=()
for ((lane=0; lane<SLURM_CPUS_PER_TASK; lane++)); do run_lane "$lane" & pids+=("$!"); done
status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done
exit "$status"
