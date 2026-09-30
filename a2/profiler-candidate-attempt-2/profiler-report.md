# Native SFA candidate profiler

Independently designed cases from upstream API/tiling/call sites; no generated design.md exists.
CPU + NPU; wait=0, warmup=5, active=5, repeat=1. Sum all op_statistic.csv Total Time(us) rows / 5.
Level1 + PipeUtilization counters are diagnostic; profiled durations are not pooled into benchmark samples.
Cases SHA256: 561c24574b5e8cfbcdf15c732600e2dc47c8fb154ec8a69dd91a666f313044e1

Profiler SHA256: a5d3cf0cf644fe7e4ed93b95e48188df87a1d8b74fde66b15a7ace88bc9c0f6b
Test SHA256: 2384e5b342b77a282b4ba8abc78ddfecbaa88037e904169addb79a0e7a18cad8
Runtime package: /mnt/workspace/sfa-nonempty-perf-20260930/runtime_candidate_a2/vllm_ascend

| Case | Query shape | DType | RoPE | Selected/query | Native per-step us | CSV |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | [1, 64, 512] | torch.float16 | 0 | [1] | 28.380600 | case_000/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190708443_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 1 | [1, 64, 512] | torch.float16 | 0 | [127] | 33.696600 | case_001/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190713354_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 2 | [1, 64, 512] | torch.float16 | 0 | [257] | 38.216800 | case_002/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190718232_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 3 | [1, 64, 512] | torch.float16 | 0 | [512] | 37.644800 | case_003/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190724137_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 4 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 47.425000 | case_004/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190729163_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 5 | [32, 64, 512] | torch.float16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 58.325200 | case_005/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190735409_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 6 | [1, 64, 512] | torch.float16 | 64 | [1] | 31.148600 | case_006/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190740182_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 7 | [1, 64, 512] | torch.float16 | 64 | [127] | 37.072800 | case_007/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190745073_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 8 | [1, 64, 512] | torch.float16 | 64 | [257] | 42.248800 | case_008/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190749967_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 9 | [1, 64, 512] | torch.float16 | 64 | [512] | 41.888800 | case_009/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190754865_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 10 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 53.181000 | case_010/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190800905_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 11 | [32, 64, 512] | torch.float16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 63.833200 | case_011/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190806182_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 12 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 28.652600 | case_012/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190812077_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 13 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 33.924600 | case_013/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190817971_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 14 | [1, 64, 512] | torch.bfloat16 | 0 | [257] | 38.948800 | case_014/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190823874_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 15 | [1, 64, 512] | torch.bfloat16 | 0 | [512] | 38.044800 | case_015/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190828781_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 16 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 49.193000 | case_016/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190834827_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 17 | [32, 64, 512] | torch.bfloat16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 58.789200 | case_017/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190841093_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 18 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 31.452600 | case_018/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190846005_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 19 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 37.460800 | case_019/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190851915_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 20 | [1, 64, 512] | torch.bfloat16 | 64 | [257] | 42.624800 | case_020/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190856821_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 21 | [1, 64, 512] | torch.bfloat16 | 64 | [512] | 42.240800 | case_021/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190901634_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 22 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 55.081200 | case_022/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190906681_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 23 | [32, 64, 512] | torch.bfloat16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 66.409400 | case_023/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190912990_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 24 | [1, 64, 512] | torch.float16 | 0 | [511] | 38.020800 | case_024/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190917876_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 25 | [1, 64, 512] | torch.float16 | 0 | [1] | 49.281000 | case_025/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190922825_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 26 | [1, 64, 512] | torch.float16 | 0 | [127] | 54.561000 | case_026/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190928788_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 27 | [1, 64, 512] | torch.float16 | 0 | [513] | 58.461200 | case_027/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190934746_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 28 | [1, 64, 512] | torch.float16 | 0 | [2048] | 81.493600 | case_028/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190940733_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 29 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 99.578000 | case_029/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190945846_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 30 | [32, 64, 512] | torch.float16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 150.471000 | case_030/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190952139_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 31 | [1, 64, 512] | torch.float16 | 64 | [511] | 41.992800 | case_031/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930190957048_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 32 | [1, 64, 512] | torch.float16 | 64 | [1] | 56.889200 | case_032/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191001996_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 33 | [1, 64, 512] | torch.float16 | 64 | [127] | 63.369200 | case_033/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191007957_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 34 | [1, 64, 512] | torch.float16 | 64 | [513] | 67.973400 | case_034/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191012939_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 35 | [1, 64, 512] | torch.float16 | 64 | [2048] | 89.421800 | case_035/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191017939_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 36 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 123.598400 | case_036/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191023047_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 37 | [32, 64, 512] | torch.float16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 167.647400 | case_037/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191030470_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 38 | [1, 64, 512] | torch.bfloat16 | 0 | [511] | 38.580800 | case_038/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191035374_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 39 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 49.473000 | case_039/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191040345_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 40 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 55.033200 | case_040/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191046298_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 41 | [1, 64, 512] | torch.bfloat16 | 0 | [513] | 58.809200 | case_041/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191052276_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 42 | [1, 64, 512] | torch.bfloat16 | 0 | [2048] | 81.181600 | case_042/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191057291_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 43 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 100.438000 | case_043/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191103413_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 44 | [32, 64, 512] | torch.bfloat16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 150.283000 | case_044/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191109784_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 45 | [1, 64, 512] | torch.bfloat16 | 64 | [511] | 42.332800 | case_045/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191115697_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 46 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 56.881200 | case_046/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191120680_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 47 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 63.245200 | case_047/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191126660_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 48 | [1, 64, 512] | torch.bfloat16 | 64 | [513] | 68.937400 | case_048/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191131641_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 49 | [1, 64, 512] | torch.bfloat16 | 64 | [2048] | 89.557800 | case_049/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191136676_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 50 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 123.846400 | case_050/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191141842_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 51 | [32, 64, 512] | torch.bfloat16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 167.551400 | case_051/752c3fdca26b44da9fd55f3c88dd3113_1323833_20260930191148334_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
