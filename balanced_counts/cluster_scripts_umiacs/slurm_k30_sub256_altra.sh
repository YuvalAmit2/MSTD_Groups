#!/bin/bash
# Replace the 20 pathological k=30 / 20000 shards with 256 nested subshards
# apiece.  320 Slurm elements x 16 lanes = 5,120 independent Altra tasks.
#SBATCH --job-name=bd-k30-sub256
#SBATCH --array=0-319
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=256M
#SBATCH --output=log/sub256_%A_%a.log

set -euo pipefail

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE"

parents=(
    0 1 2 54 55 7700 7701 7702 7720 7754
    7755 7773 15010 15400 15401 15402 15420 15454 15455 15473
)

old_n=20000
factor=256
new_n=$((old_n * factor))
outdir=out_k30_sub256
mkdir -p "$outdir"

run_lane() {
    local lane=$1 linear parent_index q parent subid out tmp
    linear=$((SLURM_ARRAY_TASK_ID * SLURM_CPUS_PER_TASK + lane))
    parent_index=$((linear / factor))
    q=$((linear % factor))
    parent=${parents[$parent_index]}
    subid=$((parent + q * old_n))
    out="$outdir/sub_${parent}_${q}.txt"

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
