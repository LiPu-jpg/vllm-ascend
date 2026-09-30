from pathlib import Path
import hashlib,json,tarfile
root=Path('/mnt/workspace/sfa-nonempty-perf-20260930/iteration-a3')
assert (root/'controller.exit').read_text().strip()=='0'
files=[p for p in root.iterdir() if p.is_file() and p.suffix in ('.json','.jsonl','.log','.exit','.xml')]
for d in root.glob('profiler-*-attempt-*'):
 if d.is_dir():files += [p for p in d.rglob('*') if p.is_file() and (p.name in ('op_statistic.csv','kernel_details.csv','profiler-report.md'))]
manifest=[dict(path=str(p.relative_to(root)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)]
(root/'collection-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
files.append(root/'collection-manifest.json')
archive=root/'collection-final.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz') as t:
 for p in files:t.add(p,arcname=str(p.relative_to(root)))
print(json.dumps(dict(count=len(files),archive=str(archive),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
