"""Remove our unstarted waiting job from the other owner's scheduler guard."""
import json
import os
from pathlib import Path
import signal

pid = 1377608
root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
words = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
assert str(root / 'controller_v1.sh').encode() in words
assert not (root / 'build.log').exists(), 'Do not cancel a running build'
assert os.getpgid(pid) == pid, 'Require our isolated process group'
(root / 'controller-v1-cancelled.json').write_text(json.dumps({
    'pid': pid,
    'reason': 'Other SFA controller guard sees our waiting controller as a foreign job; remove our unstarted waiter to avoid mutual waiting.',
    'build_started': False,
    'npu_validation_started': False,
}, indent=2))
os.killpg(pid, signal.SIGTERM)
print('CANCELLED_OWN_UNSTARTED_WAITER', pid)
