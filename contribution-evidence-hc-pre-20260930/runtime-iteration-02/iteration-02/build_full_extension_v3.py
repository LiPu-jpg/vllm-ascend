"""Build the complete native extension from the exact runtime commit.

This follows the root CMake build arguments in setup.py, without changing
setup.py, bypassing dependencies or replacing any registered operators.
The private HcPre OPP packages are built separately by csrc/build.sh.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from sysconfig import get_paths

import pybind11
import torch_npu


def main():
    root = Path('/mnt/workspace/hc-pre-reduction-20260930')
    source = root / 'full-plugin-source-v3'
    build = root / 'iteration-02/full-extension-build-v3'
    assert not source.exists(), 'Never replace an existing checkout or build'
    subprocess.run(['git', 'clone', '--local', str(root / 'full-plugin-source-v2'), str(source)], check=True)
    subprocess.run(['git', '-C', str(source), 'fetch', str(root / 'iteration-02/runtime-d50.bundle'),
                    'codex/hc-pre-vector-reduction-20260930'], check=True)
    subprocess.run(['git', '-C', str(source), 'checkout', '--detach', 'd50abbec269b1f55983f122388d608b0fab38a62'], check=True)
    build.mkdir()
    commands = [
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
    for command in commands:
        print('COMMAND', json.dumps(command), flush=True)
        subprocess.run(command, check=True)
    files = list((source / 'vllm_ascend').glob('vllm_ascend_C*.so'))
    assert len(files) == 1, files
    manifest = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in files + list((source / 'vllm_ascend').glob('libvllm_ascend_kernels.so'))}
    (build / 'binary-sha256.json').write_text(json.dumps(manifest, indent=2))
    print('FULL_NATIVE_BUILD_PASS', manifest, flush=True)


if __name__ == '__main__':
    main()
