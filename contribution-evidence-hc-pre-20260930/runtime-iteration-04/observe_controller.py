"""Read only actual descendants of this controller; omit unrelated processes."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('pid', type=int)
args = parser.parse_args()
output = subprocess.check_output(['ps', '-eo', 'pid,ppid,etimes,pcpu,stat,wchan:24,args'], text=True)
rows = {}
for line in output.splitlines()[1:]:
    parts = line.split(None, 6)
    if len(parts) == 7:
        rows[int(parts[0])] = parts
children = {args.pid}
while True:
    new = {pid for pid, parts in rows.items() if int(parts[1]) in children}
    if new <= children:
        break
    children |= new
for pid in sorted(children):
    if pid in rows:
        parts = rows[pid]
        print(' '.join(parts[:6]), parts[6][:240])
print('LIVE_CONTROLLER', args.pid in rows)
print('PROC_WCHAN', (Path('/proc') / str(args.pid) / 'wchan').read_text() if args.pid in rows else 'terminal')
