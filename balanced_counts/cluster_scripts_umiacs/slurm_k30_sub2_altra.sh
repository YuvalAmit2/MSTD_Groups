#!/bin/bash
# Split each of the 12 remaining first-level subshards another 256 ways.
# 192 Slurm elements x 16 lanes = 3,072 second-level subshards.
#SBATCH --job-name=bd-k30-sub2
#SBATCH --array=0-191
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=256M
#SBATCH --output=log/sub2_%A_%a.log

set -euo pipefail

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE"

bases=(0 1 2 54 1720054 55 27720 427720 567720 27773 395010 395454)
old_n=5120000
factor=256
new_n=$((old_n * factor))
outdir=out_k30_sub2
mkdir -p "$outdir"

run_lane() {
    local lane=$1 linear base_index q base subid out tmp
    linear=$((SLURM_ARRAY_TASK_ID * SLURM_CPUS_PER_TASK + lane))
    base_index=$((linear / factor))
    q=$((linear % factor))
    base=${bases[$base_index]}
    subid=$((base + q * old_n))
    out="$outdir/sub2_${base}_${q}.txt"
    if [[ -s "$out" ]] && grep -q "task ${subid}/${new_n}" "$out"; then
        return
    fi
    tmp="${out}.tmp.${SLURM_ARRAY_JOB_ID}.${SLURM_ARRAY_TASK_ID}.${lane}"
    ./balanced_dihedral_arm64 30 "$new_n" "$subid" 6 > "$tmp"
    mv "$tmp" "$out"
}

pids=()
for ((lane=0; lane<SLURM_CPUS_PER_TASK; lane++)); do
    run_lane "$lane" &
    pids+=("$!")
done
status=0
for pid in "${pids[@]}"; do
    wait "$pid" || status=1
done
exit "$status"
