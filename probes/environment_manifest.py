import ast,hashlib,json,platform,sys
from pathlib import Path
from importlib.metadata import version
root=Path('/mnt/workspace/sfa-nonempty-perf-20260930')
file=root/'runtime_baseline/vllm_ascend/device/device_op.py'
s=file.read_text();tree=ast.parse(s)
function=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='execute_sparse_flash_attention_process')
caches={}
for variant in ('candidate','candidate-a2'):
 for p in (root/variant/'csrc/build').rglob('CMakeCache.txt'):
  flags=[line for line in p.read_text().splitlines() if line.startswith(('CMAKE_BUILD_TYPE:','CMAKE_CXX_FLAGS_RELEASE:','CMAKE_C_FLAGS_RELEASE:','CMAKE_C_COMPILER:','CMAKE_CXX_COMPILER:'))]
  caches[str(p.relative_to(root))]=flags
record=dict(python_version=sys.version,python_executable=sys.executable,torch=version('torch'),torch_npu=version('torch-npu'),platform=platform.platform(),machine=platform.machine(),device='Ascend910B3 physical3 / 64GiB HBM',driver='25.5.0',cann='9.1.0',omp_num_threads=1,build_commands=['bash build.sh --opkernel --soc=ascend910b --ops=sparse_flash_attention -j2'],cmake_flags=caches,baseline_sfa_dispatch_ast_sha256=hashlib.sha256(ast.dump(function,include_attributes=False).encode()).hexdigest(),clock_power_control='not fixed; independent interleaved processes and all observed ranges retained',binary_traces='retained in isolated remote workspace; not published here')
(root/'environment-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
