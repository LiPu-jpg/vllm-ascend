# Correct the host-execution evidence

The completed screen-v1 controller exited0, with504 tests per package and32 balanced timing records. However, the subsequent actual-launch audit failed: every candidate q1 profile still showed20 AIC/40 AIV, rather than the expected1/2. These results are preserved, but cannot evaluate E1 scheduling effectiveness.

The private installer copied libcust_opmaster_rt2.0.so into the compat liboptiling.so file while leaving a separate older lib/linux/aarch64/libcust_opmaster_rt2.0.so (SHA3a2bc13b64fa789db46b988206967781871f2175d9ac95a5286be0a3fb9d6346) in place. Both were loaded. Library presence was an insufficient execution check.

Corrected packages restore CMake's relative compat symlink and copy fresh matched original/candidate host libraries into the actual rt2.0 destination. Kernel binaries, op API/proto and framework files remain byte-identical. The package pair differs only in the actual host library. The loaded-library verifier resolves the compat path and verifies the canonical actual host; profiler launch checks precede test/timing interpretation. No shared SDK or protected worktree was modified.

The first corrected installer stopped before any NPU call because the host library is stripped. It is retained with terminal1. The subsequent verifier checks the unstripped host object and link record, verifies host hashes against the previously validated Ninja compile-command provenance, and creates fresh v4 package paths. No build rerun was needed.

D4's head-split scheduling attribution also needs review because it used the same installation destination pattern. Its kernel-change and no-split ablation observations remain raw evidence; they cannot establish that the intended modified host head-splitting schedule executed. This does not erase measured kernel regressions, and does not justify claiming the unverified schedule is faster.

E2 remains prepared only. Do not queue its workspace reduction until E1's actual scheduling execution is established. Neither a new performance PR nor a model speedup is claimed.
