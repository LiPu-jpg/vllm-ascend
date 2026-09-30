// SPDX-License-Identifier: Apache-2.0
#include "../moe/vllm_mhc_expand/mhc_expand_params.h"
#include "../moe/vllm_mhc_expand/op_kernel/mhc_expand_kernel.h"

extern "C" __global__ __aicore__ void mhc_expand_direct(
    GM_ADDR x, GM_ADDR y, uint64_t tokens, uint64_t hidden, uint64_t mult,
    uint64_t tilesPerRow, uint64_t totalTiles, uint32_t tileLength, uint32_t tilingKey)
{
    const vllm_ascend::MhcExpandParams params{tokens, hidden, mult, tilesPerRow, totalTiles, tileLength};
    KernelMhcExpand<vllm_ascend::MhcExpandParams> op;
    op.Init(x, y, params);
    if (tilingKey == 2) {
        op.ProcessOutputTiles();
    } else {
        op.Process();
    }
}

namespace vllm_ascend {
void mhc_expand_direct_impl(void* stream, void* x, void* y, const MhcExpandLaunchConfig& config)
{
    const auto& params = config.params;
    mhc_expand_direct<<<config.blockDim, nullptr, stream>>>(
        static_cast<GM_ADDR>(x), static_cast<GM_ADDR>(y), params.tokens, params.hidden, params.mhcMult,
        params.tilesPerRow, params.totalTiles, params.tileLength, config.tilingKey);
}
}  // namespace vllm_ascend
