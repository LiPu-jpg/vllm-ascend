#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
result="$task_root/iteration-01/build-peeled"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/build.exit"' EXIT
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export C_COMPILER="$CC" CXX_COMPILER="$CXX"
export MAX_JOBS=4 CMAKE_BUILD_PARALLEL_LEVEL=4
variant="$task_root/peeled"
mkdir "$variant"
tar -xzf /mnt/workspace/upstream-csrc.tar.gz -C "$variant"
ln -s "$runtime_root/vllm-ascend/csrc/third_party/catlass" "$variant/csrc/third_party/catlass"
(cd "$variant" && patch -p1 < "$task_root/iteration-01/peeled-reduction.patch") > "$result/patch.log" 2>&1
(cd "$variant/csrc" && bash build.sh --pkg --ops=hc_pre --soc=ascend910b --vendor_name=reduction_peeled) > "$result/build.log" 2>&1
installers=("$variant/csrc/build/"*.run)
test "${#installers[@]}" = 1
bash "${installers[0]}" --install-path="$variant/opp" > "$result/install.log" 2>&1
find "$variant/opp" -name '*.o' -o -name 'libcust_opapi.so' | sort | xargs sha256sum > "$result/binary-sha256.txt"
