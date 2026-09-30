# PR #17852 CI snapshot

Code head: 5e51218dc3285dab1d58684d4804eb680fa51510. DCO, pre-commit/mypy and both CPU-UT versions (vLLM main ced6857 and v0.30.0) pass.

CI gate fails because select-tests and device suites are skipped without a run-enabling maintainer label. The failed job states: source changes require precision/full tests before merge; a maintainer must add exactly one of ready-precise (recommended), ready-all or main2main. This is a merge prerequisite, not a source test failure. Device CI is not claimed to pass. The PR remains draft for A3/device validation and review of the recorded performance regressions.

Raw job log and the status/body snapshot are retained here. Original experiment evidence remains frozen at commit 3d6558a784a368cd479a02dcf0bd0c064ee03f7d. This CI-only supplement does not alter any measurements or aggregate the extra public-script runs into the acceptance sample pool.
