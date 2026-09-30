import json
import os
from pathlib import Path

tasks = []
for p in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        args = [x.decode(errors='replace') for x in p.read_bytes().split(b'\0') if x]
        maps = (p.parent / 'maps').read_text(errors='replace')
    except OSError:
        continue
    if not args or int(p.parent.name) == os.getpid():
        continue
    exe = Path(args[0]).name
    npu_loaded = 'libtorch_npu' in maps
    compiler = exe in ('bisheng', 'cc1plus', 'cmake', 'make') or any('opc_tool/opc.py' in x for x in args)
    task_script = next((x for x in args[1:] if x.endswith(('.py', '.sh')) and x.startswith('/mnt/workspace/')), None)
    if npu_loaded or compiler or task_script:
        tasks.append(dict(pid=int(p.parent.name), exe=exe, script=task_script, npu_loaded=npu_loaded, compiler=compiler))
print(json.dumps(dict(tasks=tasks), indent=2))
