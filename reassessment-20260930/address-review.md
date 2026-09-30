# Third candidate address/synchronization review (static; NPU results pending)

The V-template merge partition is [s2GmStartOffset,s2GmLimit), within a 512-row staging tile. Let begin=(start+mte2Size)*headDimRope, end=limit*headDimRope. The entire RoPE suffix occupies the contiguous element interval [begin,end).

Each full copy reads exactly headDim elements from the already zeroed key-row UB region and advances the destination by headDim elements. The loop requires offset+headDim<=end. The only tail reads end-offset elements (<headDim), advances no further and ends exactly at end. Thus no copy touches another AIV partition or reads more than the same initialized UB key row. The host validation requires headDim512 and RoPE0/64 for this path; RoPE0 does not enter the branch. Full and tail lengths are 32-byte aligned for FP16/BF16.

The existing V->MTE3 barrier follows Duplicate. Every key and RoPE copy remains before the existing MTE3->MTE2 completion event. The caller's final events, buffer ring, valid-size updates, tiling and Cube/softmax operations are untouched. This review does not establish numerical correctness or performance; those require the planned native tests.
