import tarfile
from pathlib import Path

root = Path('/mnt/workspace/sfa-nonempty-perf-20260930')
assert not (root/'candidate-a2').exists()
(root/'candidate-a2').mkdir()
(root/'iteration-a2').mkdir()
with tarfile.open(root/'candidate-a2-csrc.tar.gz') as archive:
    archive.extractall(root/'candidate-a2', filter='data')
print('Prepared separate A2 candidate sources; A1 and baseline remain intact.')
