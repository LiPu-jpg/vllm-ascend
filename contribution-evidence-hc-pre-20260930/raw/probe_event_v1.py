"""Standalone ACLNN probe using unchanged upstream HcPre bindings and tests.

This validates the full operator but does not load the full vLLM plugin/model.
"""
import ast
import atexit
import os
import sys
from pathlib import Path

import torch
import torch_npu
from torch.utils.cpp_extension import load

ROOT = Path(__file__).resolve().parent


def record_maps():
    if "PROBE_RESULT_DIR" in os.environ:
        destination = Path(os.environ["PROBE_RESULT_DIR"])
        mappings = Path("/proc/self/maps").read_text()
        (destination / "loaded-libraries.txt").write_text("\n".join(
            line for line in mappings.splitlines() if any(name in line for name in
            ("libcust_", "libopapi", "hc_pre_reduction_probe"))))


atexit.register(record_maps)
SRC = ROOT / "baseline/csrc"
CANN = Path(os.environ["ASCEND_HOME_PATH"])
NPU = Path(torch_npu.__file__).resolve().parent
source = (SRC / "torch_binding.cpp").read_text()
begin = source.index("constexpr int64_t HC_PRE_HC_LIMIT = 4;")
end = source.index("\nvoid inplace_partial_rotary_mul_npu", begin)
cpp = source[:source.index("#include")]
cpp += '''
#include <torch/library.h>
#include <acl/acl.h>
#include <acl/acl_rt.h>
#include "aclnn_torch_adapter/op_api_common.h"
thread_local char g_hashBuf[kHashBufSize];
thread_local int g_hashOffset = 0;
'''
cpp += source[begin:end]
cpp += '''
TORCH_LIBRARY_FRAGMENT(_C_ascend, m) {
  m.def("npu_hc_pre_v2(Tensor x, Tensor hc_fn, Tensor hc_scale, Tensor hc_base, int hc_mult, int hc_sinkhorn_iters, float norm_eps, float hc_eps) -> (Tensor, Tensor, Tensor)");
  m.impl("npu_hc_pre_v2", torch::kPrivateUse1, &npu_hc_pre_v2_npu);
  m.def("npu_hc_pre_v3(Tensor x, Tensor hc_fn, Tensor hc_scale, Tensor hc_base, Tensor? pre_mix=None, int hc_mult=4, int hc_sinkhorn_iters=20, float norm_eps=1e-6, float hc_eps=1e-6) -> (Tensor, Tensor, Tensor, Tensor)");
  m.impl("npu_hc_pre_v3", torch::kPrivateUse1, &npu_hc_pre_v3_npu);
}
'''
(ROOT / "probe.cpp").write_text(cpp)
os.environ.setdefault("MAX_JOBS", "2")
load(
    name="hc_pre_reduction_probe",
    sources=[str(ROOT / "probe.cpp"), str(SRC / "aclnn_torch_adapter/NPUBridge.cpp"),
             str(SRC / "aclnn_torch_adapter/NPUStorageImpl.cpp")],
    extra_include_paths=[str(SRC), str(NPU.parent), str(CANN / "include"), str(NPU / "include")],
    extra_cflags=["-O2"],
    extra_ldflags=[f"-L{NPU / 'lib'}", "-ltorch_npu", f"-L{CANN / 'lib64'}", "-lascendcl"],
    is_python_module=False, verbose=True,
    build_directory=str(ROOT / "extension"),
)


def isolated_source(path):
    # Only the full-plugin loader is replaced; operator bodies/oracles remain.
    tree = ast.parse(path.read_text())
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.ImportFrom) and node.module == "vllm_ascend.utils"
    )]
    return ast.unparse(tree)


mode = sys.argv[1]
if mode == "compile":
    raise SystemExit(0)
if mode == "test":
    import pytest
    (ROOT / "test_isolated.py").write_text("enable_custom_op = lambda: True\n" + isolated_source(ROOT / "test_npu_hc_pre.py"))
    raise SystemExit(pytest.main(["-q", "--confcutdir", str(ROOT), str(ROOT / "test_isolated.py")] + sys.argv[2:]))
if mode == "benchmark":
    sys.argv = [str(ROOT / "hc_pre.py")] + sys.argv[2:]
    exec(compile(isolated_source(ROOT / "hc_pre.py"), str(ROOT / "hc_pre.py"), "exec"),
         {"__name__": "__main__", "enable_custom_op": lambda: True})
else:
    raise ValueError(mode)
