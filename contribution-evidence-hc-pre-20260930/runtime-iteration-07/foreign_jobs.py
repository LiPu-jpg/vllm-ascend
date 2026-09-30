"""Read actual processes; expose only PID/script/CWD, never their arguments."""
import json
from pathlib import Path
import sys
own = '/mnt/workspace/hc-pre-reduction-20260930/'
rows = []
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        words = [v.decode(errors='replace') for v in proc.joinpath('cmdline').read_bytes().split(b'\0') if v]
        if len(words) < 2 or Path(words[0]).name not in ('bash', 'sh', 'python', 'python3', 'python3.12', 'pytest'):
            continue
        if words[1] in ('-c', '-lc'):
            continue
        cwd = str(proc.joinpath('cwd').resolve())
        scripts = [v for v in words[1:] if v.endswith(('.sh', '.py'))]
        task = next((str(Path(v) if v.startswith('/') else Path(cwd) / v) for v in scripts), None)
        if task and task.startswith('/mnt/workspace/') and not task.startswith(own):
            rows.append({'pid': int(proc.name), 'script': task, 'cwd': cwd})
    except (OSError, RuntimeError):
        continue
print(json.dumps(rows, sort_keys=True))
raise SystemExit(bool(rows))
