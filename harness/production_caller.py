import torch

def _view_cache_as_operator_pages(cache: torch.Tensor, block_size: int) -> torch.Tensor:
    """Expose oversized contiguous storage pages at operator block granularity."""
    storage_block_size = cache.shape[1]
    if storage_block_size == block_size:
        return cache
    if storage_block_size % block_size:
        raise ValueError(
            f"Sparse MLA storage block size {storage_block_size} is not divisible by operator block size {block_size}."
        )
    try:
        return cache.view(-1, block_size, *cache.shape[2:])
    except RuntimeError as err:
        raise ValueError("Sparse MLA oversized storage pages must support a zero-copy operator-page view.") from err

def sparse_mla(query, cache, indices, metadata, scale):
    """Attend to original latent KV, using the platform's NoPE operator."""
    cache = _view_cache_as_operator_pages(cache, metadata.block_size)
    if metadata.smla_metadata is not None:
        # The A5 DMA merges adjacent columns. Preserve the selected set while
        # sorting token positions and moving invalid padding to the end.
        sentinel = torch.iinfo(torch.int32).max
        sorted_indices = torch.where(indices >= 0, indices, sentinel).sort(dim=-1).values
        sorted_indices = torch.where(sorted_indices == sentinel, -1, sorted_indices)
        if metadata.smla_sinks is None:
            raise RuntimeError("Sparse MLA requires persistent sinks owned by SparseMLAMetadataState.")
        # Default to the very tensors the plan in metadata.smla_metadata was
        # generated from, so plan and call always describe the same work.
        topk_length = metadata.smla_topk_length
        cu_seqlens_q = metadata.query_start_loc
        plan = metadata.smla_metadata
        # The plan has to be generated from the very tensors the operator call
        # receives: a plan built over different ones makes the kernel index past
        # what it was handed. The shape check below catches the eager case, where
        # the query is trimmed to the unpadded row count, but a replayed FULL
        # draft graph passes the padded count the plan was built for. The MTP
        # draft replays one captured graph per step, so its pre-built plan can
        # describe a different step's rows; rebuild from the indices actually
        # passed whenever the draft model is running.
        draft_model = is_forward_context_available() and getattr(get_forward_context(), "is_draft_model", False)
        if query.shape[0] != topk_length.shape[0] or draft_model:
            # Eager and piecewise steps trim the query to the unpadded token
            # count, while the plan built during metadata construction still
            # describes the padded one (graph capacity, and under data
            # parallelism the group-wide token count, which can be hundreds of
            # rows larger). cu_seqlens_q is padded for the same reason. Rebuild
            # for the rows actually being passed.
            #
            # Since this branch regenerates the plan anyway, take the top-k
            # lengths from the indices being passed rather than from the
            # prediction made before the indexer ran. The sort above left every
            # -1 at the tail of its row, so counting the non-negative entries
            # gives exactly the left-aligned prefix the operator contract asks
            # for, and unlike a prediction it cannot overshoot into the -1 tail.
            topk_length = (sorted_indices >= 0).sum(dim=-1, dtype=torch.int32).reshape(query.shape[0], -1)
            cu_seqlens_q = cu_seqlens_q.clamp(max=query.shape[0])
            plan = generate_smla_plan(
                metadata,
                query.shape[1],
                query.shape[2],
                sorted_indices.shape[-1],
                cu_seqlens_q,
                topk_length,
            )
        result = sparse_flash_mla(
            query.contiguous(),
            ori_kv=cache,
            ori_sparse_indices=sorted_indices,
            ori_block_table=metadata.block_table,
            cu_seqlens_q=cu_seqlens_q,
            seqused_ori_kv=metadata.seq_lens,
            ori_topk_length=topk_length,
            sinks=metadata.smla_sinks,
            metadata=plan,
            softmax_scale=scale,
            cmp_ratio=1,
            # Must match the mode the plan above was generated with.
            ori_mask_mode=0,
            cmp_mask_mode=0,
            ori_win_left=-1,
            ori_win_right=-1,
            layout_q="TND",
            layout_kv="PA_BBND",
            topk_value_mode=1,
            return_softmax_lse=False,
        )
    else:
        result = torch.ops._C_ascend.npu_sparse_flash_attention(
            query=query.contiguous(),
            key=cache,
            value=cache,
            sparse_indices=indices,
            scale_value=scale,
            sparse_block_size=1,
            block_table=metadata.block_table,
            actual_seq_lengths_query=metadata.query_start_loc[1:].to(torch.int32),
            actual_seq_lengths_kv=metadata.seq_lens.to(torch.int32),
            query_rope=None,
            key_rope=None,
            layout_query="TND",
            layout_kv="PA_BSND",
            sparse_mode=3,
            attention_mode=2,
            return_softmax_lse=False,
        )
    return result[0]
