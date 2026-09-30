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
        const auto npuStream = c10_npu::getCurrentNPUStream();
        const auto stream = npuStream.stream(false);
        void* input = x.data_ptr();
        void* output = y.data_ptr();
        // Snapshot pointers and launch parameters on the caller, retaining
        // storage ownership through submission without reading TensorImpl later.
        at_npu::native::OpCommand::RunOpApiV2("mhc_expand_direct",
            [input, output, config, npuStream, stream, inputStorage = x.storage(), outputStorage = y.storage()]() -> int {
                (void)inputStorage;
                (void)outputStorage;
                const c10_npu::NPUStreamGuard streamGuard(npuStream.unwrap());
                mhc_expand_direct_impl(stream, input, output, config);
                return 0;
            });
        return;
    }
#endif
    EXEC_NPU_CMD(aclnnVllmMhcExpand, x, mult, y);
}
}  // namespace vllm_ascend
