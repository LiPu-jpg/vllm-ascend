# Native SFA candidate profiler

Independently designed cases from upstream API/tiling/call sites; no generated design.md exists.
CPU + NPU; wait=0, warmup=5, active=5, repeat=1. Sum all op_statistic.csv Total Time(us) rows / 5.
Level1 + PipeUtilization counters are diagnostic; profiled durations are not pooled into benchmark samples.
Cases SHA256: 561c24574b5e8cfbcdf15c732600e2dc47c8fb154ec8a69dd91a666f313044e1

Profiler SHA256: a5d3cf0cf644fe7e4ed93b95e48188df87a1d8b74fde66b15a7ace88bc9c0f6b
Test SHA256: 2384e5b342b77a282b4ba8abc78ddfecbaa88037e904169addb79a0e7a18cad8
Runtime package: /mnt/workspace/sfa-nonempty-perf-20260930/runtime_candidate_a3/vllm_ascend

| Case | Query shape | DType | RoPE | Selected/query | Native per-step us | CSV |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | [1, 64, 512] | torch.float16 | 0 | [1] | 28.556600 | case_000/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215121870_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 1 | [1, 64, 512] | torch.float16 | 0 | [127] | 33.684600 | case_001/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215127820_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 2 | [1, 64, 512] | torch.float16 | 0 | [257] | 38.904800 | case_002/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215133744_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 3 | [1, 64, 512] | torch.float16 | 0 | [512] | 38.204800 | case_003/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215139688_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 4 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 49.497000 | case_004/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215145768_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 5 | [32, 64, 512] | torch.float16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 60.597200 | case_005/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215151062_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 6 | [1, 64, 512] | torch.float16 | 64 | [1] | 32.176600 | case_006/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215157000_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 7 | [1, 64, 512] | torch.float16 | 64 | [127] | 37.856800 | case_007/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215202915_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 8 | [1, 64, 512] | torch.float16 | 64 | [257] | 43.320800 | case_008/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215208842_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 9 | [1, 64, 512] | torch.float16 | 64 | [512] | 42.780800 | case_009/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215214771_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 10 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 55.197200 | case_010/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215220848_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 11 | [32, 64, 512] | torch.float16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 66.377400 | case_011/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215227167_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 12 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 29.924600 | case_012/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215233132_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 13 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 34.304600 | case_013/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215239061_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 14 | [1, 64, 512] | torch.bfloat16 | 0 | [257] | 40.188800 | case_014/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215244994_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 15 | [1, 64, 512] | torch.bfloat16 | 0 | [512] | 39.444800 | case_015/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215249932_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 16 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 50.185000 | case_016/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215256003_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 17 | [32, 64, 512] | torch.bfloat16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 60.733200 | case_017/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215301292_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 18 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 32.532600 | case_018/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215307238_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 19 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 39.136800 | case_019/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215313151_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 20 | [1, 64, 512] | torch.bfloat16 | 64 | [257] | 44.108800 | case_020/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215318085_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 21 | [1, 64, 512] | torch.bfloat16 | 64 | [512] | 43.196800 | case_021/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215323018_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 22 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 56.753200 | case_022/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215328097_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 23 | [32, 64, 512] | torch.bfloat16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 66.449400 | case_023/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215333451_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 24 | [1, 64, 512] | torch.float16 | 0 | [511] | 39.432800 | case_024/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215339393_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 25 | [1, 64, 512] | torch.float16 | 0 | [1] | 51.809000 | case_025/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215344359_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 26 | [1, 64, 512] | torch.float16 | 0 | [127] | 56.669200 | case_026/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215349341_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 27 | [1, 64, 512] | torch.float16 | 0 | [513] | 61.505200 | case_027/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215355338_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 28 | [1, 64, 512] | torch.float16 | 0 | [2048] | 83.069600 | case_028/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215400351_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 29 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 102.426000 | case_029/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215405466_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 30 | [32, 64, 512] | torch.float16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 154.347000 | case_030/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215411845_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 31 | [1, 64, 512] | torch.float16 | 64 | [511] | 43.720800 | case_031/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215416763_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 32 | [1, 64, 512] | torch.float16 | 64 | [1] | 60.301200 | case_032/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215421714_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 33 | [1, 64, 512] | torch.float16 | 64 | [127] | 66.253400 | case_033/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215426582_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 34 | [1, 64, 512] | torch.float16 | 64 | [513] | 71.973400 | case_034/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215431548_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 35 | [1, 64, 512] | torch.float16 | 64 | [2048] | 90.813800 | case_035/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215436550_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 36 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 126.294600 | case_036/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215441670_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 37 | [32, 64, 512] | torch.float16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 170.443400 | case_037/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215448209_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 38 | [1, 64, 512] | torch.bfloat16 | 0 | [511] | 40.152800 | case_038/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215453170_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 39 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 51.697000 | case_039/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215458146_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 40 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 56.977200 | case_040/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215504136_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 41 | [1, 64, 512] | torch.bfloat16 | 0 | [513] | 61.213200 | case_041/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215509127_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 42 | [1, 64, 512] | torch.bfloat16 | 0 | [2048] | 83.449600 | case_042/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215515182_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 43 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 103.158000 | case_043/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215521466_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 44 | [32, 64, 512] | torch.bfloat16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 155.131200 | case_044/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215527925_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 45 | [1, 64, 512] | torch.bfloat16 | 64 | [511] | 43.684800 | case_045/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215533849_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 46 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 59.285200 | case_046/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215538871_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 47 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 65.325200 | case_047/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215543883_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 48 | [1, 64, 512] | torch.bfloat16 | 64 | [513] | 71.377400 | case_048/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215549914_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 49 | [1, 64, 512] | torch.bfloat16 | 64 | [2048] | 91.057800 | case_049/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215554969_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 50 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 126.702600 | case_050/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215601169_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 51 | [32, 64, 512] | torch.bfloat16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 172.291400 | case_051/752c3fdca26b44da9fd55f3c88dd3113_1393303_20260930215607743_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
