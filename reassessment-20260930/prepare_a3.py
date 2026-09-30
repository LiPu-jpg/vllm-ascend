import hashlib,json,tarfile
from pathlib import Path
root=Path('/mnt/workspace/sfa-nonempty-perf-20260930')
inputs=root/'reassessment-20260930'
manifest=json.loads((inputs/'experiment-manifest.json').read_text())
for name in ('baseline-control','candidate-a3'):
 archive=inputs/(name+'-csrc.tar.gz')
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest[archive.name]
 target=root/name
 assert not target.exists()
 target.mkdir()
 with tarfile.open(archive) as data:data.extractall(target,filter='data')
(root/'iteration-a3').mkdir()
print('Separate unchanged-source control and third candidate prepared.')
