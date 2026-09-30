# A2 regression reassessment (2026-09-30)

All 52 cases retained. Acceptance (3 processes/build) and the two extra public-script runs (one process/build each) are separate datasets, not pooled. The first public run shows broad process drift; neither this observation nor source-path eligibility establishes a cause. Negative change = lower latency.

|Case|dtype|RoPE|Q|KV|Valid|Acceptance %|Public v1 %|Public v2 %|
|---|---|---|---|---|---|---|---|---|
|0|float16|0|1|512|1|-1.788|+8.124|-2.654|
|1|float16|0|1|512|127|+0.318|+5.318|+0.626|
|2|float16|0|1|512|257|+0.470|+7.119|-1.808|
|3|float16|0|1|512|512|-0.765|+5.005|-0.858|
|4|float16|0|32|512|127|-2.719|+5.543|-1.375|
|5|float16|0|32|512|512|-0.236|+6.410|-2.134|
|6|float16|64|1|512|1|-5.978|+0.793|-7.654|
|7|float16|64|1|512|127|-1.045|+2.716|-2.833|
|8|float16|64|1|512|257|+1.342|+5.644|-1.418|
|9|float16|64|1|512|512|-0.686|+3.702|-1.713|
|10|float16|64|32|512|127|-7.266|+1.059|-5.359|
|11|float16|64|32|512|512|-0.054|+3.727|-2.430|
|12|bfloat16|0|1|512|1|-0.198|+7.664|-1.782|
|13|bfloat16|0|1|512|127|-0.607|+6.870|-1.496|
|14|bfloat16|0|1|512|257|-0.811|+7.632|-3.513|
|15|bfloat16|0|1|512|512|+1.791|+6.468|-0.382|
|16|bfloat16|0|32|512|127|+1.921|+1.471|-1.563|
|17|bfloat16|0|32|512|512|+1.010|+1.612|+0.342|
|18|bfloat16|64|1|512|1|-5.694|+1.371|-7.495|
|19|bfloat16|64|1|512|127|-3.273|+4.238|-4.191|
|20|bfloat16|64|1|512|257|-0.595|+6.955|-2.240|
|21|bfloat16|64|1|512|512|+0.353|+4.788|-2.098|
|22|bfloat16|64|32|512|127|-1.358|-2.313|-2.654|
|23|bfloat16|64|32|512|512|+3.394|+0.894|+0.297|
|24|float16|0|1|512|511|+0.278|+6.301|-1.869|
|25|float16|0|1|4096|1|+0.086|+1.790|-1.649|
|26|float16|0|1|4096|127|+0.525|+1.632|-1.357|
|27|float16|0|1|4096|513|+1.114|+3.456|-1.469|
|28|float16|0|1|4096|2048|+0.755|+2.761|-0.563|
|29|float16|0|32|4096|127|+1.221|+0.604|+1.543|
|30|float16|0|32|4096|2048|-0.249|+1.216|-1.019|
|31|float16|64|1|512|511|-0.502|+3.747|-2.968|
|32|float16|64|1|4096|1|-7.326|-0.205|-5.352|
|33|float16|64|1|4096|127|-4.986|+4.942|-3.327|
|34|float16|64|1|4096|513|-1.063|+6.010|-1.344|
|35|float16|64|1|4096|2048|-1.097|+1.582|-1.419|
|36|float16|64|32|4096|127|-3.420|-0.925|-4.119|
|37|float16|64|32|4096|2048|-2.057|-0.689|-1.612|
|38|bfloat16|0|1|512|511|+0.282|+6.413|-1.195|
|39|bfloat16|0|1|4096|1|-0.179|+4.671|-2.404|
|40|bfloat16|0|1|4096|127|+2.908|+5.855|-0.669|
|41|bfloat16|0|1|4096|513|+0.268|+3.356|-3.854|
|42|bfloat16|0|1|4096|2048|+1.669|+2.399|-1.155|
|43|bfloat16|0|32|4096|127|-1.521|-1.351|-2.194|
|44|bfloat16|0|32|4096|2048|+0.280|-0.081|-0.108|
|45|bfloat16|64|1|512|511|-0.706|+3.852|-3.976|
|46|bfloat16|64|1|4096|1|-5.708|-1.742|-5.223|
|47|bfloat16|64|1|4096|127|-5.220|+1.472|-4.849|
|48|bfloat16|64|1|4096|513|+0.831|+4.277|-2.712|
|49|bfloat16|64|1|4096|2048|-0.986|+1.556|-2.107|
|50|bfloat16|64|32|4096|127|-1.900|-3.240|-3.905|
|51|bfloat16|64|32|4096|2048|-1.379|-1.298|-2.529|

Cases 1,17,23,29 have higher medians in all three unprofiled datasets. Case 23 is fully valid; case 40 (NoPE) has nonoverlapping per-process median ranges in acceptance but reverses direction in public v2. Source-unaffected paths therefore remain required controls; binary effects and process/device drift have not been separated.

Decision: current A2 patch is not accepted as a stable performance improvement. Draft PR remains under reassessment.

Third experiment: replace row-count division and per-copy minimum by element-addressed full key-row-sized copies and one final short tail. Reuse the identical zeroed UB row, keep all synchronization/allocations/key copies/tiling. No shape-specific allowlist or excluded cases. This is a hypothesis, not a measured fix. Rebuild unchanged baseline with the same current toolchain before comparing to detect build-control differences.

Acceptance: all previous correctness and all 52 timing cases, plus unchanged baseline control. Any reproducible regression beyond observed variation prevents promoting this patch. Raw negative samples remain visible.

Additional read-only diagnostics: exported all 104 kernel_details.csv files from the completed A2 profiler runs, SHA256 eb46eea44d2f065f5836f77f74ad12af175e216656b35d7484c149b9d136e43b. For case 6, mean AIV MTE3 counter falls 0.329 -> 0.151 us, while mean AIV scalar counter rises 4.212 -> 4.718 us. Those counters overlap and cannot be summed to latency. All52 counter table is a2-pipeline-summary.md.

ELF function-byte comparison finds 16 V-template AIV functions per dtype grow by 104--272 bytes in A2; NoPE and RoPE are runtime choices in the same V-template code. AIC function bytes also change while sizes remain equal. Layout/relocation and resource effects are possible, but this comparison does not establish a cause of the regressions. Fresh-source baseline control uses the same source base/build wrapper as candidate3. Build machinery changed since old preserved baseline (cache wrapper); shared kernel common sources are unchanged.

Third candidate now staged on cloud; no foreign controller/compiler/NPU process existed at launch. Controller PID1372465, results /mnt/workspace/sfa-nonempty-perf-20260930/iteration-a3. Two native builds, 60 numerical +96layout+2dispatcher+80DCP component cases/build, separate old/rebuilt control52 comparison and full52 B/C/C/B/B/C against rebuilt control, profiler52/build and pytest56/build planned. No improvement conclusion yet.

Unchanged-source rebuild COMPLETE: both ELF objects and both descriptors are byte-identical to preserved baseline (all4 SHA256 equal). The changed build-cache wrapper did not change these artifacts. Candidate3 compilation is in progress.
