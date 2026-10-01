"""Reserve no resources; inspect live foreign NPU tasks and their controllers."""
import json
import os
from pathlib import Path

busy = []
for p in Path('/proc').glob('[0-9]*/cmdline'):
    if int(p.parent.name) == os.getpid():
        continue
    try:
        args = [os.fsdecode(x) for x in p.read_bytes().split(b'\0') if x]
        maps = (p.parent / 'maps').read_text()
    except OSError:
        continue
    if not args:
        continue
    exe = Path(args[0]).name
    script = next((x for x in args[1:] if x.startswith('/mnt/workspace/') and x.endswith(('.py', '.sh'))), '')
    own = '/sfa-nonempty-perf-20260930/' in script
    controller = not own and 'controller' in Path(script).name
    compiler = exe in ('cmake', 'bisheng', 'cc1plus') or any('opc_tool/opc.py' in x for x in args)
    loaded = 'libtorch_npu' in maps
    if controller or compiler or loaded:
        busy.append(dict(pid=int(p.parent.name), exe=exe, script=script, controller=controller,
                         compiler=compiler, npu_loaded=loaded))
if busy:
    print(json.dumps(busy))
    raise SystemExit(75)
