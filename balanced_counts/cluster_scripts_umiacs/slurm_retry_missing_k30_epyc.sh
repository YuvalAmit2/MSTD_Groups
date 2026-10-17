#!/bin/bash
# Direct retry of the 20 k=30 tail shards that remained on 2026-09-17.
# Submit as array 0-19 on x86_64 EPYC nodes.
#SBATCH --job-name=bd-k30-epyc-tail
#SBATCH --array=0-19
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64M
#SBATCH --output=log/epyc_tail_%A_%a.log

set -euo pipefail

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE"

shards=(
    0 1 2 54 55 7700 7701 7702 7720 7754
    7755 7773 15010 15400 15401 15402 15420 15454 15455 15473
)

shard=${shards[$SLURM_ARRAY_TASK_ID]}
out="out_k30_n20000/shard_${shard}.txt"

if [[ -s "$out" ]] && grep -q 'partial:' "$out"; then
    exit 0
fi

tmp="${out}.tmp.${SLURM_ARRAY_JOB_ID}.${SLURM_ARRAY_TASK_ID}"
./balanced_dihedral 30 20000 "$shard" 6 > "$tmp"
mv "$tmp" "$out"
