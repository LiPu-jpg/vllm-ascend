// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <algorithm>
#include <limits>
#include "mhc_expand_params.h"

namespace vllm_ascend {
// Shared by ACLNN tiling and direct invocation: both execute the same partition.
inline bool MakeMhcExpandConfig(uint64_t s, uint64_t d, uint64_t m,
                               uint32_t availableCores, uint64_t ubBytes,
                               MhcExpandLaunchConfig& config)
{
    if (s == 0 || d == 0 || m == 0) {
        return false;
    }
    constexpr uint64_t MAX_ELEMENTS = std::numeric_limits<int64_t>::max() / 2;
    if (s > MAX_ELEMENTS / d || s * d > MAX_ELEMENTS / m) {
        return false;
    }
    constexpr uint64_t RESERVE = 4096;
    // Retain the source implementation's conservative tile budget.
    constexpr uint64_t BYTES_PER_ELEMENT = 12;
    constexpr uint64_t ALIGNMENT = 32;
    constexpr uint64_t MAX_TILE = 8192;
    constexpr uint64_t BYTES_PER_CORE = 32768;
    constexpr uint64_t MIN_OUTPUT_PARTITION_WIDTH = 1024;
    if (availableCores == 0 || ubBytes < RESERVE + BYTES_PER_ELEMENT * ALIGNMENT) {
        return false;
    }
    uint64_t tile = std::min(MAX_TILE, (ubBytes - RESERVE) / (BYTES_PER_ELEMENT * ALIGNMENT) * ALIGNMENT);
    const bool partitionOutput = d % 16 != 0 && d >= MIN_OUTPUT_PARTITION_WIDTH;
    const uint64_t expandedBytes = s * d * m * 2;
    const uint64_t computeCores = std::min<uint64_t>(availableCores,
        std::max(s, (expandedBytes - 1) / BYTES_PER_CORE + 1));
    const uint64_t columnsPerCore = (computeCores - 1) / s + 1;
    const uint64_t target = (d - 1) / columnsPerCore + 1;
    const bool bulk = d % 64 == 0 && d * m <= 2040 && tile >= d && tile * 2 >= (m + 1) * d;
    const uint64_t useful = bulk || partitionOutput ? tile : std::min(target, tile);
    tile = (useful + ALIGNMENT - 1) / ALIGNMENT * ALIGNMENT;
    const uint64_t perRow = (d - 1) / tile + 1;
    // Output tiles own disjoint aligned GM ranges even when row boundaries
    // are unaligned. Their input mapping is resolved inside the kernel.
    const uint64_t total = partitionOutput ? (s * d * m - 1) / tile + 1 : s * perRow;
    const uint64_t rows = bulk ? std::min<uint64_t>(16, tile * 2 / ((m + 1) * d)) : 1;
    const uint64_t tasks = bulk ? (s - 1) / rows + 1 : total;
    uint32_t cores = std::min<uint64_t>(bulk || partitionOutput ? availableCores : computeCores, tasks);
    // An unaligned row boundary can share a 32-byte output block with its neighbor.
    if (d % 16 != 0 && !partitionOutput) {
        cores = 1;
    }
    config = {{s, d, m, perRow, total, static_cast<uint32_t>(tile)}, cores,
              static_cast<uint32_t>(partitionOutput ? 2 : 1)};
    return true;
}
}  // namespace vllm_ascend
