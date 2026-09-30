// SPDX-License-Identifier: Apache-2.0
#include "vllm_mhc_expand_tiling.h"
#include "register/op_impl_registry.h"
#include "tiling_base/error_log.h"
#include "tiling/platform/platform_ascendc.h"
#include "../mhc_expand_launch_config.h"

namespace optiling {
static ge::graphStatus Tiling(gert::TilingContext* context)
{
    const auto* shape = context->GetInputShape(0);
    const auto* attrs = context->GetAttrs();
    OP_CHECK_NULL_WITH_CONTEXT(context, shape);
    OP_CHECK_NULL_WITH_CONTEXT(context, attrs);
    OP_CHECK_NULL_WITH_CONTEXT(context, context->GetPlatformInfo());
    const auto* mult = attrs->GetInt(0);
    OP_CHECK_NULL_WITH_CONTEXT(context, mult);
    const auto& x = shape->GetStorageShape();
    if (x.GetDimNum() != 2 || x.GetDim(0) <= 0 || x.GetDim(1) <= 0 || *mult <= 0) {
        return ge::GRAPH_FAILED;
    }
    const uint64_t s = x.GetDim(0), d = x.GetDim(1), m = *mult;
    auto platform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
    uint64_t ubBytes = 0;
    platform.GetCoreMemSize(platform_ascendc::CoreMemType::UB, ubBytes);
    const uint32_t availableCores = platform.GetCoreNumAiv();
    vllm_ascend::MhcExpandLaunchConfig config;
    if (!vllm_ascend::MakeMhcExpandConfig(s, d, m, availableCores, ubBytes, config)) {
        return ge::GRAPH_FAILED;
    }
    VllmMhcExpandTilingData params;
    params.set_tokens(s);
    params.set_hidden(d);
    params.set_mhcMult(m);
    params.set_tilesPerRow(config.params.tilesPerRow);
    params.set_totalTiles(config.params.totalTiles);
    params.set_tileLength(config.params.tileLength);
    context->SetTilingKey(config.tilingKey);
    context->SetBlockDim(config.blockDim);
    params.SaveToBuffer(context->GetRawTilingData()->GetData(), context->GetRawTilingData()->GetCapacity());
    context->GetRawTilingData()->SetDataSize(params.GetDataSize());
    context->GetWorkspaceSizes(1)[0] = 0;
    return ge::GRAPH_SUCCESS;
}
IMPL_OP_OPTILING(VllmMhcExpand).Tiling(Tiling);
}  // namespace optiling
