// SPDX-License-Identifier: Apache-2.0
#include "mhc_expand_kernel.h"

extern "C" __global__ __aicore__ void vllm_mhc_expand(
    GM_ADDR x, GM_ADDR y, GM_ADDR workspace, GM_ADDR tiling)
{
    GET_TILING_DATA(params, tiling);
    if (TILING_KEY_IS(1)) {
        KernelMhcExpand<VllmMhcExpandTilingData> op;
        op.Init(x, y, params);
        op.Process();
    } else if (TILING_KEY_IS(2)) {
        KernelMhcExpand<VllmMhcExpandTilingData> op;
        op.Init(x, y, params);
        op.ProcessOutputTiles();
    }
}
