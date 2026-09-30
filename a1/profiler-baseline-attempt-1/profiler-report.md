# Native SFA baseline profiler

Independently designed cases from upstream API/tiling/call sites; no generated design.md exists.
CPU + NPU; wait=0, warmup=5, active=5, repeat=1. Sum all op_statistic.csv Total Time(us) rows / 5.
Level1 + PipeUtilization counters are diagnostic; profiled durations are not pooled into benchmark samples.
Cases SHA256: 561c24574b5e8cfbcdf15c732600e2dc47c8fb154ec8a69dd91a666f313044e1

Profiler SHA256: a5d3cf0cf644fe7e4ed93b95e48188df87a1d8b74fde66b15a7ace88bc9c0f6b
Test SHA256: 2384e5b342b77a282b4ba8abc78ddfecbaa88037e904169addb79a0e7a18cad8
Runtime package: /mnt/workspace/sfa-nonempty-perf-20260930/runtime_baseline/vllm_ascend

| Case | Query shape | DType | RoPE | Selected/query | Native per-step us | CSV |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | [1, 64, 512] | torch.float16 | 0 | [1] | 28.352600 | case_000/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182649251_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 1 | [1, 64, 512] | torch.float16 | 0 | [127] | 32.284600 | case_001/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182654133_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 2 | [1, 64, 512] | torch.float16 | 0 | [257] | 36.956800 | case_002/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182700008_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 3 | [1, 64, 512] | torch.float16 | 0 | [512] | 36.616800 | case_003/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182704886_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 4 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 47.389000 | case_004/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182709911_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 5 | [32, 64, 512] | torch.float16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 56.593200 | case_005/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182715141_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 6 | [1, 64, 512] | torch.float16 | 64 | [1] | 33.508600 | case_006/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182720002_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 7 | [1, 64, 512] | torch.float16 | 64 | [127] | 37.064800 | case_007/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182724895_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 8 | [1, 64, 512] | torch.float16 | 64 | [257] | 41.160800 | case_008/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182729769_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 9 | [1, 64, 512] | torch.float16 | 64 | [512] | 40.944800 | case_009/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182734653_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 10 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 56.033200 | case_010/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182739675_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 11 | [32, 64, 512] | torch.float16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 63.153200 | case_011/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182744939_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 12 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 29.012600 | case_012/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182749826_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 13 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 32.708600 | case_013/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182755707_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 14 | [1, 64, 512] | torch.bfloat16 | 0 | [257] | 37.648800 | case_014/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182801601_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 15 | [1, 64, 512] | torch.bfloat16 | 0 | [512] | 37.192800 | case_015/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182806500_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 16 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 48.149000 | case_016/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182812546_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 17 | [32, 64, 512] | torch.bfloat16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 57.141200 | case_017/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182817821_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 18 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 34.284600 | case_018/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182822724_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 19 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 37.644800 | case_019/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182828617_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 20 | [1, 64, 512] | torch.bfloat16 | 64 | [257] | 42.020800 | case_020/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182833507_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 21 | [1, 64, 512] | torch.bfloat16 | 64 | [512] | 41.808800 | case_021/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182838398_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 22 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 57.545200 | case_022/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182843472_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 23 | [32, 64, 512] | torch.bfloat16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 63.489200 | case_023/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182848789_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 24 | [1, 64, 512] | torch.float16 | 0 | [511] | 37.660800 | case_024/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182853674_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 25 | [1, 64, 512] | torch.float16 | 0 | [1] | 49.913000 | case_025/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182858602_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 26 | [1, 64, 512] | torch.float16 | 0 | [127] | 53.901000 | case_026/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182903530_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 27 | [1, 64, 512] | torch.float16 | 0 | [513] | 58.421200 | case_027/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182908475_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 28 | [1, 64, 512] | torch.float16 | 0 | [2048] | 81.105600 | case_028/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182913459_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 29 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 101.950000 | case_029/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182918461_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 30 | [32, 64, 512] | torch.float16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 150.059000 | case_030/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182924699_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 31 | [1, 64, 512] | torch.float16 | 64 | [511] | 41.760800 | case_031/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182929585_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 32 | [1, 64, 512] | torch.float16 | 64 | [1] | 62.337200 | case_032/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182934533_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 33 | [1, 64, 512] | torch.float16 | 64 | [127] | 66.477400 | case_033/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182939496_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 34 | [1, 64, 512] | torch.float16 | 64 | [513] | 69.777400 | case_034/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182944455_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 35 | [1, 64, 512] | torch.float16 | 64 | [2048] | 90.681800 | case_035/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182949469_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 36 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 127.938600 | case_036/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930182954580_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 37 | [32, 64, 512] | torch.float16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 168.275400 | case_037/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183002050_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 38 | [1, 64, 512] | torch.bfloat16 | 0 | [511] | 37.792800 | case_038/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183006953_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 39 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 49.969000 | case_039/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183011917_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 40 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 54.309000 | case_040/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183016895_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 41 | [1, 64, 512] | torch.bfloat16 | 0 | [513] | 58.557200 | case_041/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183021876_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 42 | [1, 64, 512] | torch.bfloat16 | 0 | [2048] | 81.449600 | case_042/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183027907_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 43 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 102.646000 | case_043/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183033039_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 44 | [32, 64, 512] | torch.bfloat16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 151.635000 | case_044/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183039426_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 45 | [1, 64, 512] | torch.bfloat16 | 64 | [511] | 42.108800 | case_045/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183045328_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 46 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 62.841200 | case_046/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183050293_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 47 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 66.005400 | case_047/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183055280_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 48 | [1, 64, 512] | torch.bfloat16 | 64 | [513] | 70.269400 | case_048/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183101269_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 49 | [1, 64, 512] | torch.bfloat16 | 64 | [2048] | 90.561800 | case_049/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183106177_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 50 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 129.098600 | case_050/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183111327_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 51 | [32, 64, 512] | torch.bfloat16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 171.075400 | case_051/752c3fdca26b44da9fd55f3c88dd3113_1273778_20260930183117843_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
