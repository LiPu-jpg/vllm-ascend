"""Read-only scheduler guard for other shared-environment work."""
from pathlib import Path
import sys

shared='/mnt/workspace/mhc-validation-20260930/'
root=Path('/proc')
rows=[]
for process in root.iterdir():
    if not process.name.isdigit():continue
    try:
        args=process.joinpath('cmdline').read_bytes().split(b'\0')
        words=[a.decode(errors='replace') for a in args if a]
        if not words:continue
        # Inspect real executable arguments, not SSH command strings or grep.
        if Path(words[0]).name not in ('bash','python','python3','pytest'):continue
        if len(words)>1 and words[1]=='-c':continue
        cwd=str(process.joinpath('cwd').resolve())
        is_job=any(w.startswith(shared) and w.endswith(('.sh','.py')) for w in words[1:])
        is_job|=any(w.startswith('benchmarks/') and w.endswith('.py') for w in words[1:]) and cwd.startswith(shared)
        is_job|=Path(words[0]).name=='pytest' and cwd.startswith(shared)
        if is_job:rows.append({'pid':process.name,'command':words})
    except (OSError,RuntimeError):pass
for row in rows:print(row)
raise SystemExit(bool(rows))
