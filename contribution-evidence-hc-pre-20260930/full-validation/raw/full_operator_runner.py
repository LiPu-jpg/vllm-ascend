"""Run the unchanged entrypoint; only record import paths and library maps."""
import atexit
import json
import os
import runpy
import sys
from pathlib import Path


def record_runtime():
    result = Path(os.environ['FULL_RESULT_DIR'])
    label = os.environ['FULL_STAGE']
    names = ('vllm', 'vllm_ascend', 'vllm_ascend.utils', 'vllm_ascend.vllm_ascend_C')
    paths = {name: getattr(sys.modules.get(name), '__file__', None) for name in names}
    (result / f'{label}-module-paths.json').write_text(json.dumps(paths, indent=2))
    lines = Path('/proc/self/maps').read_text().splitlines()
    (result / f'{label}-libraries.txt').write_text('\n'.join(
        line for line in lines if any(name in line for name in ('libcust_', 'libopapi', 'vllm_ascend_C'))
    ) + '\n')


atexit.register(record_runtime)
entrypoint, sys.argv = sys.argv[1], sys.argv[1:]
if entrypoint == 'pytest':
    runpy.run_module('pytest', run_name='__main__')
else:
    runpy.run_path(entrypoint, run_name='__main__')
