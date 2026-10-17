#!/bin/bash
# Autonomous CLIP production controller. Run as one small batch job; it submits
# one 225-element child array at a time so the clip QoS 500-job limit is obeyed.
# Each child uses 225 elements x 4 CPUs = at most 900 CPU cores.
# Incomplete runs are safely resubmitted because slurm_clip_776.sh skips valid
# shard files and writes each new result atomically.
#SBATCH --job-name=bd-chain
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=256M
#SBATCH --time=2-12:00:00
#SBATCH --output=log/production_chain_%j.log

set -uo pipefail

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE" || exit 1
mkdir -p log

run_and_verify() {
    local k=$1 nshard=$2 attempt

    # A prior or dependency run may already have completed this value.
    if python3 combine_files.py "$k" "$nshard"; then
        return 0
    fi

    for attempt in 1 2 3 4 5; do
        echo "Submitting k=$k nshard=$nshard attempt=$attempt at $(date)"
        K="$k" NSHARD="$nshard" sbatch --wait \
            --partition=clip --account=clip --qos=default \
            --exclude='clip[04-06,11-14],legacy[41,43]' \
            --array=0-224%225 --cpus-per-task=4 \
            slurm_clip_776.sh || echo "Child array had failed elements; checking resumable shards"

        if python3 combine_files.py "$k" "$nshard"; then
            echo "Verified k=$k at $(date)"
            return 0
        fi
        echo "k=$k incomplete after child array; retrying completed-shard-safe run"
    done

    echo "ERROR: k=$k remains incomplete after five attempts" >&2
    return 1
}

# Verify/recover the dependency run before advancing, then execute production
# strictly in ascending order.
run_and_verify 24 1000 || exit 1
run_and_verify 25 1000 || exit 1
run_and_verify 26 1000 || exit 1
run_and_verify 27 1000 || exit 1
run_and_verify 28 2000 || exit 1
run_and_verify 29 8000 || exit 1
run_and_verify 30 20000 || exit 1

echo "All production runs verified at $(date)"
