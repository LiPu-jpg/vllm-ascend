// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <torch_npu/csrc/core/npu/NPUFunctions.h>
#ifdef VLLM_ENABLE_MHC_DIRECT
#include "tiling/platform/platform_ascendc.h"
#include "mhc_expand_launch_config.h"
#endif

namespace vllm_ascend {
inline void LaunchMhcExpand(const at::Tensor& x, int64_t mult, const at::Tensor& y)
{
#ifdef VLLM_ENABLE_MHC_DIRECT
    // Preserve the ACLNN path for caller-local core controls and non-base formats.
    if (!c10_npu::is_core_control_enabled() && IsOpInputBaseFormat(x)) {
        const auto* platform = platform_ascendc::PlatformAscendCManager::GetInstance();
        TORCH_CHECK(platform != nullptr, "mHC Expand platform information is unavailable");
        uint64_t ubBytes = 0;
        platform->GetCoreMemSize(platform_ascendc::CoreMemType::UB, ubBytes);
        MhcExpandLaunchConfig config;
        TORCH_CHECK(MakeMhcExpandConfig(x.size(0), x.size(1), mult,
                    platform->GetCoreNumAiv(), ubBytes, config), "Invalid mHC Expand launch configuration");
        // Drain pending framework submissions before launching on the caller.
        // Producers and subsequent consumers retain their stream order; device
        // execution stays asynchronous. Tensor metadata is consumed here.
        const auto stream = c10_npu::getCurrentNPUStream().stream();
        mhc_expand_direct_impl(stream, x.data_ptr(), y.data_ptr(), config);
        return;
    }
#endif
    EXEC_NPU_CMD(aclnnVllmMhcExpand, x, mult, y);
}
}  // namespace vllm_ascend
