"""Freeze completed correctness records, excluding large tensors and binaries."""

import hashlib
import json
from pathlib import Path
import shutil
import tarfile


def main():
    root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-08')
    target = root / 'terminal-source7-correctness-text-v1'
    assert not target.exists()
    for label, status in (('v2r-original-reference', '0'), ('v3-hf32-reference', '0'), ('v3b-generic', '1')):
        assert (root / f'controller-{label}.exit').read_text().strip() == status
        pid = (root / f'controller-{label}.pid').read_text().strip()
        try:
            cmd = (Path('/proc') / pid / 'cmdline').read_bytes()
        except FileNotFoundError:
            cmd = b''
        assert b'hc-pre-reduction-20260930' not in cmd
    allowed = {'.json', '.txt', '.log', '.exit', '.pid', '.py', '.sh'}
    files = set()
    for pattern in ('batch-comb0r-*', 'batch-comb1r-*', 'batch-comb2-*', 'batch-comb3-*', 'saved-baseline-boundary-comparison-v2'):
        for folder in root.glob(pattern):
            if folder.is_dir():
                files.update(p for p in folder.rglob('*') if p.is_file() and p.suffix in allowed)
    for pattern in ('controller-v2r-original-reference.*', 'controller-v3-hf32-reference.*', 'controller-v3b-generic.*', '*hf32*.json', '*generic*.json', 'corrected-reference-strict-cpu-gate-v1.log', 'saved-baseline-boundary-comparison-v*.log', 'saved-baseline-boundary-comparison-v*.exit'):
        files.update(p for p in root.glob(pattern) if p.is_file())
    for name in ('classify_generic_native_contract.py', 'compare_generic_validation.py', 'compare_nightly_hf32_reference.py', 'compare_historical_boundary_cpu.py', 'compare_historical_boundary_cpu-v1-failed.py'):
        files.add(root / name)
    assert files and all(p.stat().st_size < 8 * 1024 * 1024 for p in files)
    target.mkdir()
    manifest = {}
    for path in sorted(files):
        relative = path.relative_to(root)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest
        manifest[str(relative)] = digest
    (target / 'manifest-sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with tarfile.open(root / 'terminal-source7-correctness-text-v1.tar', 'w') as archive:
        archive.add(target, arcname=target.name)
    print('FROZEN_TEXT_RECORDS', len(manifest))
    print('SAVED_TENSORS_NOT_INCLUDED;_PER_CASE_TENSOR_DIGESTS_RETAINED')


if __name__ == '__main__':
    main()
