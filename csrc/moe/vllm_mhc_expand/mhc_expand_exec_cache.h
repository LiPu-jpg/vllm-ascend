// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <array>
#include <cstring>
#include <limits>
#include <torch_npu/csrc/core/npu/NPUFunctions.h>

namespace vllm_ascend {

// Use CANN's existing execution cache, including its address-update and lifetime
// handling. No executor or tensor pointer is retained by the adapter itself.
class MhcExpandExecCache {
public:
    MhcExpandExecCache(const at::Tensor& x, int64_t mult, const at::Tensor& y,
                      aclrtStream stream) : api_(GetApi()), stream_(stream)
    {
        // Other storage formats retain the regular ACLNN conversion path. For
        // base formats, ConvertType describes storage as one flat byte extent.
        if (!api_.Ready() || !IsOpInputBaseFormat(x) || !IsOpInputBaseFormat(y) ||
            x.unsafeGetTensorImpl()->is_wrapped_number() || !api_.canUse(OP_NAME)) {
            return;
        }
        const bool coreControl = c10_npu::is_core_control_enabled();
        const uint64_t aic = coreControl
            ? c10_npu::GetResInCurrentThread(c10_npu::acl::ACL_RT_DEV_RES_CUBE_CORE) : 0;
        const uint64_t aiv = coreControl
            ? c10_npu::GetResInCurrentThread(c10_npu::acl::ACL_RT_DEV_RES_VECTOR_CORE) : 0;
        // A separate domain prevents collisions with other operators sharing
        // CANN's cache. Include every varying ACL tensor descriptor field and
        // execution setting; addresses are registered separately below.
        constexpr char domain[] = "vllm_mhc_expand_cache_v1";
        static_assert(sizeof(domain) <= 4 * sizeof(uint64_t));
        std::memcpy(key_.data(), domain, sizeof(domain));
        const std::array<uint64_t, 20> fields = {
            static_cast<uint64_t>(x.size(0)), static_cast<uint64_t>(x.size(1)),
            static_cast<uint64_t>(mult), static_cast<uint64_t>(x.scalar_type()),
            static_cast<uint64_t>(x.storage_offset()), x.storage().nbytes(),
            static_cast<uint64_t>(x.stride(0)), static_cast<uint64_t>(x.stride(1)),
            static_cast<uint64_t>(y.storage_offset()), y.storage().nbytes(),
            static_cast<uint64_t>(y.stride(0)), static_cast<uint64_t>(y.stride(1)),
            static_cast<uint64_t>(y.stride(2)), static_cast<uint64_t>(x.get_device()),
            reinterpret_cast<uintptr_t>(stream),
            static_cast<uint64_t>(at::globalContext().deterministicAlgorithms()),
            static_cast<uint64_t>(coreControl), aic, aiv, 1};
        std::memcpy(key_.data() + 4, fields.data(), sizeof(fields));
        void* input = const_cast<void*>(x.storage().data());
        void* output = const_cast<void*>(y.storage().data());
        api_.init();
        active_ = true;
        api_.addAddress(input);
        api_.addAddress(output);
        auto* bytes = reinterpret_cast<uint8_t*>(key_.data());
        api_.setKey(bytes, sizeof(key_));
        executor_ = api_.find(bytes, sizeof(key_), &workspaceSize_);
        // A miss keeps this scope active while EXEC_NPU_CMD builds the executor
        // and lets CANN populate the cache, as in the torch_npu dispatch path.
    }

    ~MhcExpandExecCache()
    {
        if (active_) {
            api_.uninit();
        }
    }
    MhcExpandExecCache(const MhcExpandExecCache&) = delete;
    MhcExpandExecCache& operator=(const MhcExpandExecCache&) = delete;

    bool RunIfHit()
    {
        if (executor_ == nullptr) {
            return false;
        }
        at::Tensor workspace;
        if (workspaceSize_ != 0) {
            TORCH_CHECK(workspaceSize_ <= static_cast<uint64_t>(std::numeric_limits<int64_t>::max()),
                        "mHC Expand workspace size overflows int64");
            const auto options = at::TensorOptions(torch_npu::utils::get_npu_device_type()).dtype(at::kByte);
            workspace = at::empty({static_cast<int64_t>(workspaceSize_)}, options);
        }
        const auto execute = api_.execute;
        const auto stream = stream_;
        const auto executor = executor_;
        const auto workspaceSize = workspaceSize_;
        at_npu::native::OpCommand::RunOpApiV2(OP_NAME,
            [workspace, workspaceSize, executor, stream, execute]() -> int {
                void* data = workspace.defined() ? const_cast<void*>(workspace.storage().data()) : nullptr;
                const auto status = execute(data, workspaceSize, executor, stream);
                TORCH_CHECK(status == 0, "cached aclnnVllmMhcExpand failed: ", aclGetRecentErrMsg());
                return status;
            });
        return true;
    }

private:
    static constexpr const char* OP_NAME = "aclnnVllmMhcExpand";
    struct Api {
        using Init = void (*)();
        using CanUse = bool (*)(const char*);
        using SetKey = void (*)(uint8_t*, size_t);
        using AddAddress = void (*)(void*);
        using Find = aclOpExecutor* (*)(uint8_t*, size_t, uint64_t*);
        using Execute = int (*)(void*, uint64_t, aclOpExecutor*, aclrtStream);
        Init init, uninit;
        CanUse canUse;
        SetKey setKey;
        AddAddress addAddress;
        Find find;
        Execute execute;
        bool Ready() const
        {
            return init && uninit && canUse && setKey && addAddress && find && execute;
        }
    };
    static const Api& GetApi()
    {
        static const Api api{
            reinterpret_cast<Api::Init>(GetOpApiFuncAddr("InitPTACacheThreadLocal")),
            reinterpret_cast<Api::Init>(GetOpApiFuncAddr("UnInitPTACacheThreadLocal")),
            reinterpret_cast<Api::CanUse>(GetOpApiFuncAddr("CanUsePTACache")),
            reinterpret_cast<Api::SetKey>(GetOpApiFuncAddr("SetPTACacheHashKey")),
            reinterpret_cast<Api::AddAddress>(GetOpApiFuncAddr("AddTensorAddrToCachedList")),
            reinterpret_cast<Api::Find>(GetOpApiFuncAddr("PTAFindExecCache")),
            reinterpret_cast<Api::Execute>(GetOpApiFuncAddr(OP_NAME))};
        return api;
    }
    const Api& api_;
    aclrtStream stream_;
    std::array<uint64_t, 24> key_{};
    aclOpExecutor* executor_ = nullptr;
    uint64_t workspaceSize_ = 0;
    bool active_ = false;
};

}  // namespace vllm_ascend
