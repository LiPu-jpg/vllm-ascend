"""Export only completed text evidence; keep tensors/profiler binaries private."""
import hashlib,json,tarfile
from pathlib import Path
root=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-01')
selected=[]
for child in root.iterdir():
    if child.is_dir() and ((child/'run.exit').exists() or (child/'build.exit').exists()):
        selected.append(child)
manifest=[];public=[]
for child in selected:
    for path in sorted(child.rglob('*')):
        if not path.is_file():continue
        manifest.append({'path':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        if path.suffix in ('.log','.txt','.csv','.xml','.json','.exit') and path.name!='trace_view.json':public.append(path)
for path in root.iterdir():
    if path.is_file() and path.suffix in ('.py','.sh','.patch'):public.append(path)
for name in ('profile-summary.json','profile-controller.exit','profile-v2-controller.exit','profile-controller.log','profile-v2-controller.log','validation-controller.log','validation-controller.exit','validation-v2-controller.log','validation-v2-controller.exit','validation-v3-controller.log','validation-v3-controller.exit'):
    path=root/name
    if path.exists():public.append(path)
metadata=root/'snapshot-manifest.json';metadata.write_text(json.dumps(manifest,indent=2));public.append(metadata)
archive=root/'iteration-01-text-snapshot.tar'
with tarfile.open(archive,'w') as tar:
    for path in sorted(set(public)):tar.add(path,arcname=str(path.relative_to(root)))
print('snapshot_bytes',archive.stat().st_size,'sha256',hashlib.sha256(archive.read_bytes()).hexdigest(),'files',len(public))
