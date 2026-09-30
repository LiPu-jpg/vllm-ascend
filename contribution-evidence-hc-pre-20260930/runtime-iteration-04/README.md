# Contiguous Cast candidate: rejected for latency optimization

The independent candidate combines Cast rows when both source and destination
strides equal the logical width; padded rows retain their original conversions.
Baseline is `11682d1e341d161a4129a58863f39a912846f71d`; runtime candidate is
`5983ac07f62095c1e7fa725e0b7f9ce692e8d5f1`. Both complete native extensions and
private OPP packages were freshly built with identical flags. The actual opened
kernel objects are recorded under `completed-text-v1/cast3-trace-*`.
No competition source was copied; the existing CANN OSLA 2.0 header is preserved.

## Performance conclusion

| Complete HcPre comparison | Geometric mean speedup | Faster / slower | Maximum slowdown |
| --- | ---: | ---: | ---: |
| Graph ABBA | 0.978565531 | 4 / 24 | 7.538737% |
| Graph BAAB | 0.994634162 | 9 / 19 | 4.209548% |
| Same-code graph A/A | 0.982400785 | 5 / 23 | 5.195160% |
| Eager ABBA | 1.056090783 | 15 / 13 | 4.572575% |
| Same-code eager A/A | 1.015264779 | 13 / 15 | 2.583321% |

Both graph orders regress overall. Eager process pairs give 0.985613738 and
1.079384045, so the pooled apparent gain is not stable. A/A variation is retained
and is not subtracted to manufacture candidate gains. All 28 cases, all warmups
and samples, round medians, process medians and slowdown cases remain available.
Each arm has two independent processes and 150 measured samples per case.
Profiling retains 28 cases with 60 HcPre observations each. Vector duration
slightly decreases, but scalar and kernel durations vary or regress; a shorter
critical path is not established. Profiler timings are not benchmark samples.

## Correctness and integration scope

- Normal full-plugin nightly collection: 41/41 per variant, unchanged thresholds.
- Actual GLM decoder methods: 24/24 per variant; serialized outputs match.
- Boundaries: 45/60 CPU cases pass in each variant. Identical failures remain;
  candidate additionally has six cross-process parity failures at t1/d7169.
  None is counted as passed. Previous identical-baseline tail instability does
  not establish candidate correctness.
- Standard DummyModelLoader four-layer BF16 GLM eager and graph results match:
  eight requests, 64 tokens and 320 finite logprobs per arm, maximum difference 0.
  Both use the identical independent packed-convolution prerequisite from #17828
  in private sources. This is synthetic integration, not checkpoint accuracy.
- Actual model graph traces contain 14 aclmdlRIExecuteAsync events and 112 graph
  HcPre kernels plus 24 eager kernels per arm. No model throughput is measured.

Ascend 910B3 physical NPU 3/logical 0, CANN 9.1.0, torch 2.10.0+cpu,
torch_npu 2.10.0.post4 and vLLM `ced6857afa0ea7b2e3f0846a62e1394e90f15607`.
The exact scripts, guards, paths, refs, build hashes and driver hashes are retained.
All three controllers terminated with exit 0; boundary jobs retain exit 1.
The terminal snapshot contains 1,199 text files, gzip size 8,605,693 bytes,
SHA256 `6e6b089c673eccdfd0072c93446eb8dc48e2cc7517d1327eed7bac918cdd348b`.
Tensor files and binary profiler records remain on the cloud; text hashes and
traces are published. `published-file-manifest.json` covers every copied file.

The later local merge of upstream `5fa57c55bb37861d3da0274fbf7a28d15d745b87`
is not cloud validation of that revision. This candidate is excluded from
PR #17821. The inference optimization goal remains unfinished.

See [journal.md](journal.md), the five `*-summary.json` comparisons,
[profile-summary.json](profile-summary.json),
[actual-model-graph-summary.json](actual-model-graph-summary.json) and the
reproduction controllers. Analyse graph ABBA using the same all-sample analyzer:

```bash
python ../runtime-iteration-03/analyze_comparison.py \
  --baseline completed-text-v1/cast1-graph-baseline-a/data/results.json \
    completed-text-v1/cast1-graph-baseline-b/data/results.json \
  --candidate completed-text-v1/cast1-graph-candidate-a/data/results.json \
    completed-text-v1/cast1-graph-candidate-b/data/results.json \
  --output reproduced-graph-abba.json --label contiguous-cast-graph-abba
```
