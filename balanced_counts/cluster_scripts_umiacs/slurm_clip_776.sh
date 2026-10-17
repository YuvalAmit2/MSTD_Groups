#!/bin/bash
# CLIP/Nexus launcher: 225 array elements x 4 independent workers = 900 cores.
# The clip partition QoS limits users to 500 submitted jobs, so using multiple
# workers per array element is necessary to exceed 500 concurrent cores.
#
# Submit with an explicit array range, partition, account, and CPU count; see
# the validation and production commands in INSTRUCTIONS.txt.
#SBATCH --job-name=balanced-dihedral
#SBATCH --array=0-224
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64M
#SBATCH --time=24:00:00
#SBATCH --requeue
#SBATCH --output=log/element_%A_%a.log

set -euo pipefail

K=${K:-30}
NSHARD=${NSHARD:-20000}
SPLIT=${SPLIT:-6}
BINARY=${BINARY:-./balanced_dihedral}
OUT=out_k${K}_n${NSHARD}
mkdir -p "$OUT"

: "${SLURM_ARRAY_TASK_ID:?run this as a Slurm job array}"
: "${SLURM_ARRAY_TASK_MIN:?missing Slurm array minimum}"
: "${SLURM_ARRAY_TASK_MAX:?missing Slurm array maximum}"

ARRAY_INDEX=$((SLURM_ARRAY_TASK_ID - SLURM_ARRAY_TASK_MIN))
ARRAY_SIZE=$((SLURM_ARRAY_TASK_MAX - SLURM_ARRAY_TASK_MIN + 1))
WORKERS=${SLURM_CPUS_PER_TASK:-4}
LOCAL_WORKERS=$((ARRAY_SIZE * WORKERS))
SHARD_OFFSET=${SHARD_OFFSET:-0}
GLOBAL_WORKERS=${GLOBAL_WORKERS:-$LOCAL_WORKERS}

if ((SHARD_OFFSET < 0 || SHARD_OFFSET + LOCAL_WORKERS > GLOBAL_WORKERS)); then
    echo "invalid shard worker range: offset=$SHARD_OFFSET local=$LOCAL_WORKERS global=$GLOBAL_WORKERS" >&2
    exit 2
fi

run_lane() {
    local lane=$1 slot s f tmp
    slot=$((SHARD_OFFSET + ARRAY_INDEX * WORKERS + lane))
    for ((s = slot; s < NSHARD; s += GLOBAL_WORKERS)); do
        f="$OUT/shard_${s}.txt"
        if [[ -s "$f" ]] && grep -q 'partial:' "$f"; then
            continue
        fi
        tmp="$f.tmp.${SLURM_ARRAY_JOB_ID}.${SLURM_ARRAY_TASK_ID}.${lane}"
        "$BINARY" "$K" "$NSHARD" "$s" "$SPLIT" > "$tmp"
        mv "$tmp" "$f"
    done
}

pids=()
for ((lane = 0; lane < WORKERS; lane++)); do
    run_lane "$lane" &
    pids+=("$!")
done

status=0
for pid in "${pids[@]}"; do
    wait "$pid" || status=1
done
exit "$status"
