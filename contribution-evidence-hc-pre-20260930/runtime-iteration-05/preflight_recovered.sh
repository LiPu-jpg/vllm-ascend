#!/usr/bin/env bash
set -eo pipefail
root=/mnt/workspace/hc-pre-reduction-20260930
python "$root/iteration-05/foreign_jobs.py"
source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
npu-smi info
for variant in baseline candidate; do
    git -C "$root/short-div-source-$variant" rev-parse HEAD
    git -C "$root/short-div-source-$variant" status --short
done
