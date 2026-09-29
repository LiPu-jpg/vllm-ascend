// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <limits>
#include <torch_npu/csrc/core/npu/NPUFunctions.h>

namespace vllm_ascend {

// Run ACLNN preparation and submission together on the framework's queue thread.
// The enclosing callback owns x/y until submission and preserves the caller's stream.
inline int ExecuteMhcExpand(const at::Tensor& x, int64_t mult, const at::Tensor& y,
                            c10_npu::NPUStream npuStream, aclrtStream stream)
{
    const c10_npu::NPUStreamGuard streamGuard(npuStream.unwrap());
    using Query = int (*)(const aclTensor*, int64_t, const aclTensor*, uint64_t*, aclOpExecutor**);
    using Execute = int (*)(void*, uint64_t, aclOpExecutor*, aclrtStream);
    static const auto getWorkspace = reinterpret_cast<Query>(
        GetOpApiFuncAddr("aclnnVllmMhcExpandGetWorkspaceSize"));
    static const auto execute = reinterpret_cast<Execute>(GetOpApiFuncAddr("aclnnVllmMhcExpand"));
    static const auto initMemory = reinterpret_cast<InitHugeMemThreadLocal>(
        GetOpApiFuncAddr("InitHugeMemThreadLocal"));
    static const auto uninitMemory = reinterpret_cast<UnInitHugeMemThreadLocal>(
        GetOpApiFuncAddr("UnInitHugeMemThreadLocal"));
    static const auto releaseMemory = reinterpret_cast<ReleaseHugeMem>(GetOpApiFuncAddr("ReleaseHugeMem"));
    TORCH_CHECK(getWorkspace && execute, "mHC Expand ACLNN API is unavailable");
    if (initMemory) {
        initMemory(nullptr, false);
    }
    struct MemoryScope {
        UnInitHugeMemThreadLocal finish;
        ~MemoryScope() { if (finish) finish(nullptr, false); }
    } memoryScope{uninitMemory};
    struct Resources {
        aclTensor* input = nullptr;
        aclTensor* output = nullptr;
        ReleaseHugeMem release = nullptr;
        ~Resources()
        {
            if (input) Release(input);
            if (output) Release(output);
            if (release) release(nullptr, false);
        }
    } resources;
    resources.release = releaseMemory;
    resources.input = ConvertType(x);
    resources.output = ConvertType(y);
    uint64_t workspaceSize = 0;
    aclOpExecutor* executor = nullptr;
    const auto workspaceStatus = getWorkspace(resources.input, mult, resources.output, &workspaceSize, &executor);
    TORCH_CHECK(workspaceStatus == 0, "aclnnVllmMhcExpandGetWorkspaceSize failed: ", aclGetRecentErrMsg());
    at::Tensor workspace;
    if (workspaceSize != 0) {
        TORCH_CHECK(workspaceSize <= static_cast<uint64_t>(std::numeric_limits<int64_t>::max()),
                    "mHC Expand workspace size overflows int64");
        workspace = at::empty({static_cast<int64_t>(workspaceSize)}, x.options().dtype(at::kByte));
    }
    void* data = workspace.defined() ? const_cast<void*>(workspace.storage().data()) : nullptr;
    const auto status = execute(data, workspaceSize, executor, stream);
    TORCH_CHECK(status == 0, "aclnnVllmMhcExpand failed: ", aclGetRecentErrMsg());
    return status;
}

inline void LaunchMhcExpand(const at::Tensor& x, int64_t mult, const at::Tensor& y)
{
    // Preserve the existing caller-side path for thread-local core controls and
    // non-base storage formats. The asynchronous path copies only base formats.
    if (c10_npu::is_core_control_enabled() || !IsOpInputBaseFormat(x)) {
        EXEC_NPU_CMD(aclnnVllmMhcExpand, x, mult, y);
        return;
    }
    const auto npuStream = c10_npu::getCurrentNPUStream();
    const auto stream = npuStream.stream(false);
    at_npu::native::OpCommand::RunOpApiV2("aclnnVllmMhcExpand",
        [x, mult, y, npuStream, stream]() -> int {
            return ExecuteMhcExpand(x, mult, y, npuStream, stream);
        });
}

}  // namespace vllm_ascend
