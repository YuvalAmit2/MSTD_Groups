#!/bin/bash
# Post-maintenance safety pass. Completed subshards are detected and skipped.
#SBATCH --job-name=bd-sub256-fallback
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=128M
#SBATCH --time=3-00:00:00
#SBATCH --output=log/sub256_fallback_%j.log

set -euo pipefail

HERE="${SLURM_SUBMIT_DIR:-$PWD}"   # was an absolute path on the UMIACS file system
cd "$HERE"

sbatch --wait \
    --partition=scavenger-aarch64 --account=scavenger \
    --qos=scavenger-aarch64 --nodelist='oasis[00-12,14-36,38]' \
    --array=0-319%320 --time=2-20:00:00 --requeue \
    slurm_k30_sub256_altra.sh

python3 combine_k30_sub256.py
