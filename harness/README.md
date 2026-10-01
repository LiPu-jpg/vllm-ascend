# Supplemental development harnesses

These Python/shell harnesses were developed for the recorded experiments; they are distributed under the adjacent Apache-2.0 license. The two production helper bodies used by `production_caller.py` come from upstream `vllm_ascend/attention/sfa_v1.py` at the tested base (Apache-2.0). No recovered contest implementation is included. Harness bytes are preserved as executed; native upstream CANN sources remain in the upstream repository under their own notices.

Controller scripts retain the original isolated workspace/runtime paths. Adapt those paths to independent installations, preserve input captures and versions, and run one NPU job at a time. `run_checked_v3.py` records canonical loaded host hashes. Scripts import the adjacent retained test_helper.py fixtures, which are independently written supplemental helpers and not upstream-existing tests at the tested base. Keep those executed helper bytes and the original upstream revision. The public 40-case benchmark in the source branch is the simplest standalone reproduction method.

`retained-private-tests` includes the two public files alongside the 198-case supplementary sparse-index file exactly as executed. Their file presence here does not add the private file to the source PR. Preserve the final 418-public + 198-private distinction.
