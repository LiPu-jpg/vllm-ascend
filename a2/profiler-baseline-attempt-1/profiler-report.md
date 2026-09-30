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
| 0 | [1, 64, 512] | torch.float16 | 0 | [1] | 28.716600 | case_000/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185809124_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 1 | [1, 64, 512] | torch.float16 | 0 | [127] | 32.456600 | case_001/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185814057_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 2 | [1, 64, 512] | torch.float16 | 0 | [257] | 37.384800 | case_002/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185819939_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 3 | [1, 64, 512] | torch.float16 | 0 | [512] | 37.092800 | case_003/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185824830_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 4 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 49.933000 | case_004/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185829841_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 5 | [32, 64, 512] | torch.float16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 59.097200 | case_005/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185835101_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 6 | [1, 64, 512] | torch.float16 | 64 | [1] | 33.988600 | case_006/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185840977_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 7 | [1, 64, 512] | torch.float16 | 64 | [127] | 37.448800 | case_007/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185846866_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 8 | [1, 64, 512] | torch.float16 | 64 | [257] | 41.656800 | case_008/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185852766_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 9 | [1, 64, 512] | torch.float16 | 64 | [512] | 41.524800 | case_009/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185858650_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 10 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 58.333200 | case_010/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185904681_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 11 | [32, 64, 512] | torch.float16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 64.741200 | case_011/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185910955_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 12 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 28.792600 | case_012/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185915847_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 13 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 32.724600 | case_013/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185921752_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 14 | [1, 64, 512] | torch.bfloat16 | 0 | [257] | 37.068800 | case_014/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185927662_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 15 | [1, 64, 512] | torch.bfloat16 | 0 | [512] | 36.952800 | case_015/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185933570_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 16 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 47.769000 | case_016/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185938613_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 17 | [32, 64, 512] | torch.bfloat16 | 0 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 56.429200 | case_017/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185943907_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 18 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 34.068600 | case_018/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185948724_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 19 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 37.508800 | case_019/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185954636_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 20 | [1, 64, 512] | torch.bfloat16 | 64 | [257] | 42.000800 | case_020/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930185959532_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 21 | [1, 64, 512] | torch.bfloat16 | 64 | [512] | 41.696800 | case_021/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190005449_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 22 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 57.189200 | case_022/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190011525_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 23 | [32, 64, 512] | torch.bfloat16 | 64 | [512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512, 512] | 66.661400 | case_023/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190017848_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 24 | [1, 64, 512] | torch.float16 | 0 | [511] | 37.940800 | case_024/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190023762_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 25 | [1, 64, 512] | torch.float16 | 0 | [1] | 49.861000 | case_025/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190028600_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 26 | [1, 64, 512] | torch.float16 | 0 | [127] | 54.057000 | case_026/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190034570_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 27 | [1, 64, 512] | torch.float16 | 0 | [513] | 58.445200 | case_027/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190040541_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 28 | [1, 64, 512] | torch.float16 | 0 | [2048] | 80.785600 | case_028/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190046539_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 29 | [32, 64, 512] | torch.float16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 103.502000 | case_029/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190052629_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 30 | [32, 64, 512] | torch.float16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 151.607000 | case_030/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190059956_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 31 | [1, 64, 512] | torch.float16 | 64 | [511] | 42.512800 | case_031/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190105883_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 32 | [1, 64, 512] | torch.float16 | 64 | [1] | 62.169200 | case_032/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190111861_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 33 | [1, 64, 512] | torch.float16 | 64 | [127] | 66.381400 | case_033/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190116819_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 34 | [1, 64, 512] | torch.float16 | 64 | [513] | 69.933400 | case_034/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190122783_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 35 | [1, 64, 512] | torch.float16 | 64 | [2048] | 90.613800 | case_035/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190128808_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 36 | [32, 64, 512] | torch.float16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 128.626600 | case_036/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190134930_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 37 | [32, 64, 512] | torch.float16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 171.059400 | case_037/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190141407_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 38 | [1, 64, 512] | torch.bfloat16 | 0 | [511] | 37.412800 | case_038/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190147324_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 39 | [1, 64, 512] | torch.bfloat16 | 0 | [1] | 49.693000 | case_039/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190153300_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 40 | [1, 64, 512] | torch.bfloat16 | 0 | [127] | 53.561000 | case_040/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190158285_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 41 | [1, 64, 512] | torch.bfloat16 | 0 | [513] | 58.341200 | case_041/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190204269_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 42 | [1, 64, 512] | torch.bfloat16 | 0 | [2048] | 80.465600 | case_042/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190209287_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 43 | [32, 64, 512] | torch.bfloat16 | 0 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 101.618000 | case_043/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190215336_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 44 | [32, 64, 512] | torch.bfloat16 | 0 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 150.051000 | case_044/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190221713_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 45 | [1, 64, 512] | torch.bfloat16 | 64 | [511] | 42.000800 | case_045/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190227643_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 46 | [1, 64, 512] | torch.bfloat16 | 64 | [1] | 62.033200 | case_046/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190232632_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 47 | [1, 64, 512] | torch.bfloat16 | 64 | [127] | 65.933400 | case_047/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190237607_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 48 | [1, 64, 512] | torch.bfloat16 | 64 | [513] | 70.085400 | case_048/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190242612_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 49 | [1, 64, 512] | torch.bfloat16 | 64 | [2048] | 90.653800 | case_049/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190247647_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 50 | [32, 64, 512] | torch.bfloat16 | 64 | [127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127] | 127.830600 | case_050/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190252809_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
| 51 | [32, 64, 512] | torch.bfloat16 | 64 | [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048] | 169.971400 | case_051/752c3fdca26b44da9fd55f3c88dd3113_1307309_20260930190300300_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv |
