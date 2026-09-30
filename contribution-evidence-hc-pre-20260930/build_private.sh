#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
mkdir "$task_root"
trap 'status=$?; echo "$status" > "$task_root/build.exit"' EXIT
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/venv/bin/activate"
export PATH="/home/developer/.local/bin:$PATH"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export C_COMPILER="$CC" CXX_COMPILER="$CXX"
export MAX_JOBS=4 CMAKE_BUILD_PARALLEL_LEVEL=4
for variant in baseline candidate; do
    mkdir "$task_root/$variant"
    tar -xzf /mnt/workspace/upstream-csrc.tar.gz -C "$task_root/$variant"
    ln -s "$runtime_root/vllm-ascend/csrc/third_party/catlass" "$task_root/$variant/csrc/third_party/catlass"
    if [[ "$variant" == candidate ]]; then
        (cd "$task_root/$variant" && patch -p1 < /mnt/workspace/candidate.patch)
    fi
    (cd "$task_root/$variant/csrc" && bash build.sh --pkg --ops=hc_pre --soc=ascend910b --vendor_name="reduction_$variant") \
        > "$task_root/$variant/build.log" 2>&1
    installers=("$task_root/$variant/csrc/build/"*.run)
    test "${#installers[@]}" = 1
    bash "${installers[0]}" --install-path="$task_root/$variant/opp" \
        > "$task_root/$variant/install.log" 2>&1
done
