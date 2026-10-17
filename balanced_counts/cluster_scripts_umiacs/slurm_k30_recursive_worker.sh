#!/bin/bash
# Generic packed worker for one recursive subdivision generation.
# ARRAY_SIZE is supplied by the controller; every element uses 16 lanes.
#SBATCH --job-name=bd-k30-recursive
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=256M
#SBATCH --output=log/recursive_%A_%a.log

set -euo pipefail
: "${PARENTS_FILE:?}"
: "${PARENT_N:?}"
: "${GEN:?}"

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE"
mapfile -t parents < "$PARENTS_FILE"

factor=256
new_n=$((PARENT_N * factor))
total=$((${#parents[@]} * factor))
outdir="out_k30_recursive/gen_${GEN}"
mkdir -p "$outdir"

run_lane() {
    local lane=$1 linear parent_index q parent child out tmp
    linear=$((SLURM_ARRAY_TASK_ID * SLURM_CPUS_PER_TASK + lane))
    ((linear < total)) || return 0
    parent_index=$((linear / factor))
    q=$((linear % factor))
    parent=${parents[$parent_index]}
    child=$((parent + q * PARENT_N))
    out="$outdir/task_${child}.txt"
    if [[ -s "$out" ]] && grep -q "task ${child}/${new_n}" "$out"; then
        return 0
    fi
    tmp="${out}.tmp.${SLURM_ARRAY_JOB_ID}.${SLURM_ARRAY_TASK_ID}.${lane}"
    ./balanced_dihedral_arm64 30 "$new_n" "$child" 6 > "$tmp"
    mv "$tmp" "$out"
}

pids=()
for ((lane=0; lane<SLURM_CPUS_PER_TASK; lane++)); do
    run_lane "$lane" &
    pids+=("$!")
done
status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done
exit "$status"
