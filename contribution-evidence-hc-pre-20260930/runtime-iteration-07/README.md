# Input-prefetch candidate: retained correctness and HF32 diagnostics

This archive contains correctness results, build metadata and independent HF32
diagnostics. It contains no performance results for this candidate. Numerical
failures are retained and must not be counted as passed validation.

The production runtime base is `62e05feb3db521230c27714ad4347bd0d9d38f1a`.
The built input-prefetch change is `b712c2b2bda7603af7ec5c3386726ff30979a2b5`;
the documented source head is `b8f067cd3f01c78fc2e7d35f12385a948dac1a26`.
The change queues input tiles earlier using the existing buffers. It is separate
from the later comb-copy batching candidate; these results do not validate that
candidate. The source-ledger.json is an original preparation record: its test
count and unbuilt status are superseded by actual terminal results below.

The environment uses NPU 3/chip 0 (910B3), CANN 9.1.0, Python 3.12.14,
torch 2.10.0, torch_npu 2.10.0.post4 and the real FLA package. Native extensions
and private OPP packages were built for both arms with matched flags; command
metadata and binary hashes are included. The build controller exited 1 because
a foreign job appeared after both builds completed. terminal-build-integrity.json
verifies the completed binaries without rewriting that exit status. Validation
used a fresh guarded idle window and verified the actual private HcPre object
loads before recording correctness results.

## Correctness recorded through the production plugin

Normal nightly collection used the repository conftests, without loader stubs or
AST rewriting. Each arm collected 93 tests: 81 passed and the same 12 failed.
All 16 added graph tests for updated activations and external coefficients
passed. Workflow exit 0 means all requested results were recorded with failures,
not that all tests passed.

| Coverage per arm | Baseline CPU passes | Candidate CPU passes | Other findings |
| --- | ---: | ---: | --- |
| 72 finite fixtures | 60 | 60 | All 48 real hidden-size cases pass; 12 h128 failures |
| 28 exact benchmark inputs | 16 | 16 | Repeat, eager/graph and cross-arm parity checks pass |
| 60 boundary cases | 45 | 45 | Candidate has 6 cross-process byte mismatches; baseline has none |
| 24 actual decoder-method cases | 24 | 24 | Six CPU checks per case; eager/graph parity passes |

The h128 failures include nonfinite and repeat/graph discrepancies. The twelve
amplified signed benchmark cases fail the original CPU reference in both arms.
Neither category is erased. All twelve correctness phases passed the device,
other-job and foreign-job postguards. Decoder-method coverage is not a full
standard-loader model smoke. No model smoke or throughput gain is established
for this candidate.

## Independent HF32 diagnostics

The original test reference remains 10 fractional bits with bit-mask truncation.
An 18-case production diagnostic ruled out that representation for the observed
910B3 path. A subsequent 42-case diagnostic covered positive and negative
coefficients, even/odd anchors, rounding boundaries and exponent carry for both
4096 and 7168 hidden sizes. All outputs were finite; private kernel selection and
all job/device guards passed. At the diagnostic alignment threshold of 2e-6:

| Reference model | Aligned cases |
| --- | ---: |
| 10-bit truncation | 6/42 |
| 11-bit truncation | 24/42 |
| 11-bit nearest, ties to even | 40/42 |
| 11-bit nearest, ties away from zero | 42/42 |
| 19-bit truncation | 12/42 |
| Full FP32 | 12/42 |

The aligned model's maximum absolute pre-output difference is 2.98023224e-8.
This is limited normal-coefficient diagnostic evidence on the verified 910B3
baseline, not certification of special values or other architectures. The
diagnostic alignment threshold does not change any nightly accuracy threshold.
Full saved-output sensitivity analysis is prepared but has not completed. Its
first invocation stopped during PyTorch backend auto-loading because libhccl.so
was not on the CPU process's library path. The retained CPU-only controller uses
TORCH_DEVICE_BACKEND_AUTOLOAD=0 and has not started because a foreign SFA test
was active. That CPU-only analysis is not full plugin integration verification.

The SDK mapping archive contains paths, hashes and line ranges only. Licensed
SDK source excerpts remain private and are not redistributed here. The mapping
connects advanced SetHF32 transMode=1 to the low-level control bit; the observed
rounding behavior is established by hardware controls, not inferred from the
ambiguous low-level SDK comments.

## Reproduction and archive limits

Use the exact source revisions above and the recorded build commands, configure
the same runtime dependencies, and run the guarded controller scripts from the
original private task root. They check actual other processes before starting,
refuse duplicate controller launches, and retain phase exit codes and raw data.
The full extension uses production registration, including keyword-only V3
parameters. Timing controllers are prepared but remain unstarted; a strict CPU
accuracy gate must be resolved before performance comparison.

All published text is inventoried by archive-sha256.json. Run
`python verify_archive.py` from this directory to check file integrity. Full
build logs, installed binaries, the Git bundle and tensor .pt files remain in
the private cloud evidence directory. Their hashes appear in the original
records. Hash inventory verifies archive integrity only; it does not certify
correctness, kernel speed or model acceleration.
