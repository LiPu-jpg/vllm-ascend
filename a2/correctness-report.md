# Candidate A2 correctness

- New native boundary, varlen, multi-tile and graph-replay pytest: 56 passed, including empty rows.
- Independent FP64 attention/LSE: 60 cases passed the project attention tolerances, with all three native outputs byte-identical to baseline.
- Expanded 96 layout/block/mode cases: all three outputs byte-identical. Eight baseline nonempty LSE reference failures remain failures in both builds: [22, 23, 46, 47, 70, 71, 94, 95]. The other 88 pass the independent reference. Two actual production-dispatch mode checks pass.
- Actual Triton DCP remap -> actual dispatcher single-receiver component: 80 cases per build pass exact remapping, independent reference and all three output-byte comparisons. Distributed collectives and model inference are not exercised.
- Public benchmark execution: 52 cases per build complete; candidate outputs match baseline bytes and all input hashes match the six-process acceptance workload.
- Generic per-element MERE/MARE near-zero criteria fail many upstream baseline attention values. No claim of passing those criteria is made, and they are not relaxed to report a win. Project tolerance checks and byte-preserving parity are reported separately.

The new pytest checks empty outputs with a tiny absolute tolerance; it does not fix or assert valid softmax statistics for empty rows. The baseline empty-row statistics defect belongs to #17823.
