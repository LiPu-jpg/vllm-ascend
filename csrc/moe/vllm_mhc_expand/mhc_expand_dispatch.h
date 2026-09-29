// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <limits>
#include <memory>

namespace vllm_ascend {

// Match the framework's lightweight op-api submission path. Keep ACLNN tensor
// conversion and workspace discovery on the caller, as in EXEC_NPU_CMD_V1.
inline void LaunchMhcExpand(const at::Tensor& x, int64_t mult, const at::Tensor& y)
{
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
    const auto stream = c10_npu::getCurrentNPUStream().stream(false);
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
        at::Tensor inputOwner, outputOwner, workspace;
        ReleaseHugeMem release = nullptr;
        ~Resources()
        {
            if (input) Release(input);
            if (output) Release(output);
            if (release) release(nullptr, false);
        }
    };
    // The submission may execute later on the framework's queue thread. Keep
    // descriptors and all storage alive through completion, including errors.
    auto resources = std::make_shared<Resources>();
    resources->release = releaseMemory;
    resources->inputOwner = x;
    resources->outputOwner = y;
    resources->input = ConvertType(x);
    resources->output = ConvertType(y);
    uint64_t workspaceSize = 0;
    aclOpExecutor* executor = nullptr;
    const auto workspaceStatus = getWorkspace(resources->input, mult, resources->output, &workspaceSize, &executor);
    TORCH_CHECK(workspaceStatus == 0, "aclnnVllmMhcExpandGetWorkspaceSize failed: ", aclGetRecentErrMsg());
    if (workspaceSize != 0) {
        TORCH_CHECK(workspaceSize <= static_cast<uint64_t>(std::numeric_limits<int64_t>::max()),
                    "mHC Expand workspace size overflows int64");
        const auto options = at::TensorOptions(torch_npu::utils::get_npu_device_type()).dtype(at::kByte);
        resources->workspace = at::empty({static_cast<int64_t>(workspaceSize)}, options);
    }
    at_npu::native::OpCommand::RunOpApiV2("aclnnVllmMhcExpand",
        [resources, workspaceSize, stream, executor]() -> int {
            void* data = resources->workspace.defined()
                ? const_cast<void*>(resources->workspace.storage().data()) : nullptr;
            const auto status = execute(data, workspaceSize, executor, stream);
            TORCH_CHECK(status == 0, "aclnnVllmMhcExpand failed: ", aclGetRecentErrMsg());
            return status;
        });
}

}  // namespace vllm_ascend
