#!/bin/bash
# Coordinate three disjoint CPU-only shard pools: 900 non-scavenger CLIP
# cores, 880 preemptible x86 CB​CB/Quics cores, and 5,920 preemptible ARM64
# Oasis cores. Owners can reclaim scavenger nodes and Slurm requeues those
# elements. Completed shards are detected and skipped.
#SBATCH --job-name=bd-3pool-chain
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64M
#SBATCH --time=1-12:00:00
#SBATCH --output=log/production_dual_chain_%j.log

set -uo pipefail

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE" || exit 1
mkdir -p log

run_and_verify() {
    local k=$1 nshard=$2 attempt clip_pid scav_pid oasis_pid

    if python3 combine_files.py "$k" "$nshard"; then
        return 0
    fi

    for attempt in 1 2 3 4 5; do
        echo "Submitting three pools k=$k nshard=$nshard attempt=$attempt at $(date)"

        K="$k" NSHARD="$nshard" GLOBAL_WORKERS=7700 SHARD_OFFSET=0 \
            sbatch --wait --partition=clip --account=clip --qos=default \
            --exclude='clip[04-06,11-14],legacy[41,43]' \
            --array=0-224%225 --cpus-per-task=4 --mem=64M \
            slurm_clip_776.sh &
        clip_pid=$!

        K="$k" NSHARD="$nshard" GLOBAL_WORKERS=7700 SHARD_OFFSET=900 \
            sbatch --wait --partition=scavenger --account=scavenger --qos=scavenger \
            --nodelist='cbcb[00-21,30],quics00' \
            --array=0-219%220 --cpus-per-task=4 --mem=64M --requeue \
            slurm_clip_776.sh &
        scav_pid=$!

        K="$k" NSHARD="$nshard" GLOBAL_WORKERS=7700 SHARD_OFFSET=1780 \
            BINARY=./balanced_dihedral_arm64 \
            sbatch --wait --partition=scavenger-aarch64 --account=scavenger \
            --qos=scavenger-aarch64 --nodelist='oasis[00-12,14-36,38]' \
            --array=0-369%370 --cpus-per-task=16 --mem=256M --requeue \
            slurm_clip_776.sh &
        oasis_pid=$!

        wait "$clip_pid" || echo "CLIP child had failed elements; checking shards"
        wait "$scav_pid" || echo "x86 scavenger child was interrupted; checking resumable shards"
        wait "$oasis_pid" || echo "Oasis child was interrupted; checking resumable shards"

        if python3 combine_files.py "$k" "$nshard"; then
            echo "Verified k=$k at $(date)"
            return 0
        fi
        echo "k=$k incomplete; retrying both completed-shard-safe pools"
    done

    echo "ERROR: k=$k remains incomplete after five attempts" >&2
    return 1
}

run_and_verify 29 8000 || exit 1
run_and_verify 30 20000 || exit 1
echo "All production runs verified at $(date)"
