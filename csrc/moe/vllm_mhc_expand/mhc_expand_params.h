// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <cstdint>

namespace vllm_ascend {
struct MhcExpandParams {
    uint64_t tokens;
    uint64_t hidden;
    uint64_t mhcMult;
    uint64_t tilesPerRow;
    uint64_t totalTiles;
    uint32_t tileLength;
};

struct MhcExpandLaunchConfig {
    MhcExpandParams params;
    uint32_t blockDim;
    uint32_t tilingKey;
};

void mhc_expand_direct_impl(void* stream, void* x, void* y, const MhcExpandLaunchConfig& config);
}  // namespace vllm_ascend
