"""Build matched complete native extensions from exact baseline/candidate Git."""
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
    iteration = root / 'iteration-03'
    refs = json.loads((iteration / 'revisions.json').read_text())
    for variant, revision in refs.items():
        source = root / ('optional-pre-source-' + variant)
        build = iteration / ('full-extension-build-' + variant)
        assert not source.exists() and not build.exists(), 'Never replace prior builds'
        subprocess.run(['git', 'clone', '--local', str(root / 'full-plugin-source-v3'), str(source)], check=True)
        subprocess.run(['git', '-C', str(source), 'fetch', str(iteration / 'optional-pre.bundle'), 'HEAD'], check=True)
        subprocess.run(['git', '-C', str(source), 'checkout', '--detach', revision], check=True)
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
        print('FULL_NATIVE_BUILD_PASS', variant, revision, manifest, flush=True)


if __name__ == '__main__':
    main()
