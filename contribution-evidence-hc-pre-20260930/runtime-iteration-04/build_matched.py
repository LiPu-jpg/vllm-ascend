"""Build fresh matched HcPre OPP packages and complete native extensions."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from sysconfig import get_paths

import pybind11
import torch_npu

root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-04'
refs = json.loads((iteration / 'revisions.json').read_text())
for variant, revision in refs.items():
    source = root / ('cast-source-' + variant)
    build = iteration / ('full-extension-build-' + variant)
    assert not source.exists() and not build.exists(), 'Do not replace prior sources/builds'
    subprocess.run(['git', 'clone', '--local', str(root / 'optional-pre-source-baseline'), str(source)], check=True)
    subprocess.run(['git', '-C', str(source), 'fetch', str(iteration / 'contiguous-cast-incremental.bundle'), 'HEAD'], check=True)
    subprocess.run(['git', '-C', str(source), 'checkout', '--detach', revision], check=True)
    build.mkdir()
    catlass = source / 'csrc/third_party/catlass'
    if not catlass.exists():
        catlass.parent.mkdir(parents=True, exist_ok=True)
        catlass.symlink_to('/mnt/workspace/mhc-validation-20260930/vllm-ascend/csrc/third_party/catlass')
    commands = [
        ['bash', 'build.sh', '--pkg', '--ops=hc_pre', '--soc=ascend910b', '--vendor_name=cast_' + variant],
        ['cmake', '-S', str(source), '-B', str(build), '-DCMAKE_BUILD_TYPE=Release',
         '-DCMAKE_EXPORT_COMPILE_COMMANDS=1', '-DCMAKE_C_COMPILER=/usr/bin/gcc-13',
         '-DCMAKE_CXX_COMPILER=/usr/bin/g++-13', '-DASCEND_HOME_PATH=' + os.environ['ASCEND_HOME_PATH'],
         '-DPYTHON_EXECUTABLE=' + sys.executable, '-DPYTHON_INCLUDE_PATH=' + get_paths()['include'],
         '-DCMAKE_PREFIX_PATH=' + pybind11.get_cmake_dir(), '-DSOC_VERSION=ascend910b1',
         '-DTORCH_NPU_PATH=' + str(Path(torch_npu.__file__).parent),
         '-DCMAKE_INSTALL_PREFIX=' + str(source / 'vllm_ascend')],
        ['cmake', '--build', str(build), '--target', 'vllm_ascend_C', '--parallel', '2'],
        ['cmake', '--install', str(build)],
    ]
    (build / 'commands.json').write_text(json.dumps(commands, indent=2))
    subprocess.run(commands[0], cwd=source / 'csrc', check=True)
    installers = list((source / 'csrc/build').glob('*.run'))
    assert len(installers) == 1, installers
    install = ['bash', str(installers[0]), '--install-path=' + str(source / 'opp')]
    (build / 'opp-install-command.json').write_text(json.dumps(install, indent=2))
    subprocess.run(install, check=True)
    for command in commands[1:]:
        subprocess.run(command, check=True)
    files = list((source / 'vllm_ascend').glob('vllm_ascend_C*.so'))
    files += list((source / 'vllm_ascend').glob('libvllm_ascend_kernels.so'))
    kernels = list((source / 'opp').rglob('HcPre_*.o'))
    assert len(files) == 2 and kernels, (files, kernels)
    manifest = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in files + kernels}
    (build / 'binary-sha256.json').write_text(json.dumps(manifest, indent=2))
    print('MATCHED_NATIVE_AND_OPP_BUILD_PASS', variant, revision, manifest, flush=True)
