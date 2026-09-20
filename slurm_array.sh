#!/bin/bash
#SBATCH --job-name=balanced-dihedral
#SBATCH --array=0-999              # overridden by --array on the sbatch line
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=256M                 # the program uses well under 1 MB
#SBATCH --time=12:00:00
#SBATCH --output=log/element_%a.log
#
#   mkdir -p log
#   gcc -O3 -march=native -funroll-loops -o balanced_dihedral balanced_dihedral.c
#   K=30 NSHARD=20000 sbatch --array=0-999%256 slurm_array.sh
#   python3 combine_files.py 30 20000
#
# SPLIT defaults to 6 and normally needs no setting.  See INSTRUCTIONS.txt for
# the shard count to use with each k.
#
# The %N on the sbatch line is how many elements run at once, i.e. how many cores
# the run occupies.  Each array element runs NSHARD/ARRAY_SIZE shards in
# sequence, so NSHARD can be far larger than the cluster's MaxArraySize.  Each shard writes its own small
# result file and finished shards are skipped, so resubmitting the identical
# sbatch command resumes an interrupted or partially failed run.  Shards are
# independent and deterministic; nothing is shared between them.
#
# Other schedulers: replace SLURM_ARRAY_TASK_ID / _MIN / _MAX with
# $PBS_ARRAY_INDEX (PBS Pro), $SGE_TASK_ID (SGE, 1-based) or $LSB_JOBINDEX (LSF).

set -euo pipefail
K=${K:-30}
NSHARD=${NSHARD:-20000}
SPLIT=${SPLIT:-6}
OUT=out_k${K}_n${NSHARD}
mkdir -p "$OUT"

: "${SLURM_ARRAY_TASK_ID:?run this as a job array (sbatch slurm_array.sh)}"
ARRAY_SIZE=$(( SLURM_ARRAY_TASK_MAX - SLURM_ARRAY_TASK_MIN + 1 ))

for (( s = SLURM_ARRAY_TASK_ID - SLURM_ARRAY_TASK_MIN; s < NSHARD; s += ARRAY_SIZE )); do
    f="$OUT/shard_${s}.txt"
    if [[ -s "$f" ]] && grep -q partial: "$f"; then
        continue                                   # already done, resuming
    fi
    ./balanced_dihedral "$K" "$NSHARD" "$s" "$SPLIT" > "$f.tmp"
    mv "$f.tmp" "$f"                               # atomic; no half-written files
done
