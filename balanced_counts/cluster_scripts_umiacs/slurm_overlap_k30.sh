#!/bin/bash
# Overlap k=30 with the already-running k=29 arrays. CLIP and x86 scavenger
# fit under their per-user 500-job QoS limits immediately. Oasis k=30 is
# submitted once no more than 130 of its 370 k=29 elements remain, so adding
# another 370 elements cannot exceed that limit.
#SBATCH --job-name=bd-k30-overlap
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64M
#SBATCH --time=1-12:00:00
#SBATCH --output=log/k30_overlap_%j.log

set -uo pipefail

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE" || exit 1
mkdir -p log

if python3 combine_files.py 29 8000 && python3 combine_files.py 30 20000; then
    echo "k=29 and k=30 were already complete at $(date)"
    exit 0
fi

submit_clip() {
    K=30 NSHARD=20000 GLOBAL_WORKERS=7700 SHARD_OFFSET=0 \
        sbatch --wait --partition=clip --account=clip --qos=default \
        --exclude='clip[04-06,11-14],legacy[41,43]' \
        --array=0-224%225 --cpus-per-task=4 --mem=64M \
        slurm_clip_776.sh
}

submit_x86_scavenger() {
    K=30 NSHARD=20000 GLOBAL_WORKERS=7700 SHARD_OFFSET=900 \
        sbatch --wait --partition=scavenger --account=scavenger --qos=scavenger \
        --nodelist='cbcb[00-21,30],quics00' \
        --array=0-219%220 --cpus-per-task=4 --mem=64M --requeue \
        slurm_clip_776.sh
}

submit_oasis() {
    K=30 NSHARD=20000 GLOBAL_WORKERS=7700 SHARD_OFFSET=1780 \
        BINARY=./balanced_dihedral_arm64 \
        sbatch --wait --partition=scavenger-aarch64 --account=scavenger \
        --qos=scavenger-aarch64 --nodelist='oasis[00-12,14-36,38]' \
        --array=0-369%370 --cpus-per-task=16 --mem=256M --requeue \
        slurm_clip_776.sh
}

echo "Starting early k=30 CLIP and x86 scavenger pools at $(date)"
submit_clip & clip_pid=$!
submit_x86_scavenger & x86_pid=$!

while :; do
    oasis_k29=$(squeue -r -h -j 7545522 -o '%i' 2>/dev/null | wc -l)
    echo "$(date): unfinished Oasis k=29 elements=$oasis_k29"
    if ((oasis_k29 <= 130)); then
        echo "Oasis QoS has room; starting Oasis k=30"
        submit_oasis & oasis_pid=$!
        break
    fi
    sleep 30
done

wait "$clip_pid" || echo "CLIP k=30 array had failures; shards remain resumable"
wait "$x86_pid" || echo "x86 scavenger k=30 array was interrupted; shards remain resumable"
wait "$oasis_pid" || echo "Oasis k=30 array was interrupted; shards remain resumable"

# The post-maintenance fallback safely resubmits missing shards if either
# aggregate is incomplete.
echo "k=29 aggregate status at $(date)"
python3 combine_files.py 29 8000 || true
echo "k=30 aggregate status at $(date)"
python3 combine_files.py 30 20000 || exit 1
