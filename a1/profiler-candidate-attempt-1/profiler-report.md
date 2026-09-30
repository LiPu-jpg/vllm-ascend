# Native SFA candidate profiler

Independently designed cases from upstream API/tiling/call sites; no generated design.md exists.
CPU + NPU; wait=0, warmup=5, active=5, repeat=1. Sum all op_statistic.csv Total Time(us) rows / 5.
Level1 + PipeUtilization counters are diagnostic; profiled durations are not pooled into benchmark samples.
Cases SHA256: 561c24574b5e8cfbcdf15c732600e2dc47c8fb154ec8a69dd91a666f313044e1

Profiler SHA256: a5d3cf0cf644fe7e4ed93b95e48188df87a1d8b74fde66b15a7ace88bc9c0f6b
Test SHA256: 2384e5b342b77a282b4ba8abc78ddfecbaa88037e904169addb79a0e7a18cad8
Runtime package: /mnt/workspace/sfa-nonempty-perf-20260930/runtime_candidate/vllm_ascend

| Case | Query shape | DType | RoPE | Selected/query | Native per-step us | CSV |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | [1, 64, 512] | torch.float16 | 0 | [1] | 29.152600 | case_000/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183201147_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 1 | [1, 64, 512] | torch.float16 | 0 | [127] | 33.616600 | case_001/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183206079_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 2 | [1, 64, 512] | torch.float16 | 0 | [257] | 38.764800 | case_002/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183210971_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 3 | [1, 64, 512] | torch.float16 | 0 | [512] | 38.100800 | case_003/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183215871_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 4 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 47.985000 | case_004/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183220891_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 5 | [32, 64, 512] | torch.float16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 58.037200 | case_005/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183227161_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 6 | [1, 64, 512] | torch.float16 | 64 | [1] | 32.212600 | case_006/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183232063_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 7 | [1, 64, 512] | torch.float16 | 64 | [127] | 37.028800 | case_007/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183236963_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 8 | [1, 64, 512] | torch.float16 | 64 | [257] | 42.644800 | case_008/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183241855_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 9 | [1, 64, 512] | torch.float16 | 64 | [512] | 41.920800 | case_009/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183247762_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 10 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 54.849200 | case_010/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183253829_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 11 | [32, 64, 512] | torch.float16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 64.905200 | case_011/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183259117_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 12 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 29.204600 | case_012/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183305016_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 13 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 33.736600 | case_013/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183310902_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 14 | [1, 64, 512] | torch.bfloat16 | 0 | [257] | 38.316800 | case_014/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183315796_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 15 | [1, 64, 512] | torch.bfloat16 | 0 | [512] | 38.044800 | case_015/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183320687_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 16 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 49.017000 | case_016/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183326720_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 17 | [32, 64, 512] | torch.bfloat16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 59.113200 | case_017/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183332997_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 18 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 32.396600 | case_018/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183337908_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 19 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 36.932800 | case_019/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183342799_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 20 | [1, 64, 512] | torch.bfloat16 | 64 | [257] | 42.300800 | case_020/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183347690_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 21 | [1, 64, 512] | torch.bfloat16 | 64 | [512] | 42.244800 | case_021/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183352593_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 22 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 55.301200 | case_022/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183357644_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 23 | [32, 64, 512] | torch.bfloat16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 64.989400 | case_023/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183402936_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 24 | [1, 64, 512] | torch.float16 | 0 | [511] | 38.736800 | case_024/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183407840_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 25 | [1, 64, 512] | torch.float16 | 0 | [1] | 50.685000 | case_025/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183412780_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 26 | [1, 64, 512] | torch.float16 | 0 | [127] | 54.885000 | case_026/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183417718_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 27 | [1, 64, 512] | torch.float16 | 0 | [513] | 59.445200 | case_027/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183422663_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 28 | [1, 64, 512] | torch.float16 | 0 | [2048] | 82.029600 | case_028/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183427643_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 29 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 105.254200 | case_029/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183432745_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 30 | [32, 64, 512] | torch.float16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 152.079000 | case_030/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183439053_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 31 | [1, 64, 512] | torch.float16 | 64 | [511] | 42.240800 | case_031/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183443951_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 32 | [1, 64, 512] | torch.float16 | 64 | [1] | 58.429200 | case_032/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183448910_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 33 | [1, 64, 512] | torch.float16 | 64 | [127] | 63.229200 | case_033/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183453770_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 34 | [1, 64, 512] | torch.float16 | 64 | [513] | 68.761400 | case_034/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183458743_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 35 | [1, 64, 512] | torch.float16 | 64 | [2048] | 91.181800 | case_035/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183503748_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 36 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 126.866600 | case_036/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183508877_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 37 | [32, 64, 512] | torch.float16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 170.483400 | case_037/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183515103_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 38 | [1, 64, 512] | torch.bfloat16 | 0 | [511] | 38.156800 | case_038/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183519997_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 39 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 51.013000 | case_039/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183524967_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 40 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 54.701000 | case_040/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183529943_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 41 | [1, 64, 512] | torch.bfloat16 | 0 | [513] | 59.429200 | case_041/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183535922_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 42 | [1, 64, 512] | torch.bfloat16 | 0 | [2048] | 82.077600 | case_042/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183540949_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 43 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 106.786200 | case_043/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183546072_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 44 | [32, 64, 512] | torch.bfloat16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 152.343000 | case_044/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183552428_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 45 | [1, 64, 512] | torch.bfloat16 | 64 | [511] | 41.876800 | case_045/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183558342_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 46 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 58.257200 | case_046/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183603317_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 47 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 62.873200 | case_047/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183608301_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 48 | [1, 64, 512] | torch.bfloat16 | 64 | [513] | 68.385400 | case_048/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183614287_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 49 | [1, 64, 512] | torch.bfloat16 | 64 | [2048] | 90.265800 | case_049/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183619331_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 50 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 127.742600 | case_050/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183625493_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 51 | [32, 64, 512] | torch.bfloat16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 171.187400 | case_051/752c3fdca26b44da9fd55f3c88dd3113_1288812_20260930183632990_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
