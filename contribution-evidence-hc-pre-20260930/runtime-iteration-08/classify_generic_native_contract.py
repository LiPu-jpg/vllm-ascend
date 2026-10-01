"""Classify retained errors against the actual native contract; no NPU calls."""

import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root = Path('/mnt/workspace/hc-pre-reduction-20260930')
    iteration = root / 'iteration-08'
    assert (iteration / 'controller-v3b-generic.exit').read_text().strip() == '1'
    assert 'BATCH_COMB_GENERIC_WIDTH_RESULTS_RECORDED_WITH_FAILURES' not in (
        iteration / 'controller-v3b-generic.log').read_text()
    expected_heads = {
        'baseline': '62e05feb3db521230c27714ad4347bd0d9d38f1a',
        'candidate': 'd64140c62797ebddea73b2cf091a3590b4956d99',
    }
    expected_cases = {
        f'hc{width}-t{tokens}-signed{signed}-i{iters}'
        for width in (1, 3, 8)
        for tokens in (1, 17)
        for signed in (0, 1)
        for iters in (1, 3)
    }
    records, sources = {}, {}
    for arm, expected_head in expected_heads.items():
        source = root / f'batch-comb-source-{arm}'
        head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        assert head == expected_head
        assert subprocess.check_output(['git', '-C', str(source), 'diff', 'HEAD', '--', 'csrc/torch_binding.cpp']) == b''
        binding_path = source / 'csrc/torch_binding.cpp'
        binding = binding_path.read_text()
        for required in (
            'constexpr int64_t HC_PRE_HC_LIMIT = 4;',
            'TORCH_CHECK(hc_mult == HC_PRE_HC_LIMIT, "hc_mult only supports ", HC_PRE_HC_LIMIT, ", actual ", hc_mult, ".");',
        ):
            assert required in binding
        folder = iteration / f'batch-comb3-generic-{arm}'
        subprocess.run(['python3', str(iteration / 'validate_postguards.py'), str(folder)], check=True)
        rows = json.loads((folder / 'data/results.json').read_text())
        keyed = {row['case']: row for row in rows}
        assert len(rows) == len(keyed) == 24 and set(keyed) == expected_cases
        for case, row in keyed.items():
            width = int(case.split('-')[0][2:])
            assert row['errors'] == [f'RuntimeError:hc_mult only supports 4, actual {width}.']
            assert row['cpu_accuracy_pass'] is False and row['cpu_metrics'] == []
            assert len(row['input_sha256']) == 4
        records[arm] = keyed
        sources[arm] = {'head': head, 'binding_sha256': hashlib.sha256(binding_path.read_bytes()).hexdigest()}
    for case in expected_cases:
        assert records['baseline'][case]['input_sha256'] == records['candidate'][case]['input_sha256']
    report = {
        'scope': 'CPU inspection of completed production API rejection records; no new NPU execution',
        'classification': 'All 24 inputs per arm are outside the native hc_mult=4 contract and were rejected identically.',
        'sources': sources,
        'original_controller_exit': 1,
        'original_comparison_kept_failed': True,
        'positive_generic_width_correctness_coverage': 0,
        'performance_or_model_speedup_proved': False,
        'all_recorded_inputs_and_errors_verified': True,
    }
    target = iteration / 'generic-native-contract-classification-v1.json'
    with target.open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
