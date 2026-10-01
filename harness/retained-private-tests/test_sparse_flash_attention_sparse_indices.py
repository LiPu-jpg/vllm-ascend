# SPDX-License-Identifier: Apache-2.0
"""Exercise sparse-index traversal across tiles, pages and graph inputs."""

import pytest
import torch
import torch_npu  # noqa: F401

from vllm_ascend.utils import enable_custom_op

pytestmark = pytest.mark.skipif("910" not in torch.npu.get_device_name(0), reason="Requires an A2/A3 NPU")


def make_inputs(dtype, sparse_capacity, sparse_block_size, mode, page_size):
    torch.manual_seed(930)
    query_lengths, kv_lengths = [2, 1], [256, 1024]
    heads, head_dim, rope_dim = 64, 512, 64
    capacity = ((1024 + page_size - 1) // page_size) * page_size
    query = torch.randn(3, heads, head_dim, dtype=dtype)
    query_rope = torch.randn(3, heads, rope_dim, dtype=dtype)
    key = torch.randn(2, capacity, 1, head_dim, dtype=dtype)
    rope = torch.randn(2, capacity, 1, rope_dim, dtype=dtype)
    order = torch.randperm(2 * capacity // page_size)
    table = order.reshape(2, -1).int()
    pages = torch.empty(2 * capacity // page_size, page_size, 1, head_dim, dtype=dtype)
    rope_pages = torch.empty(*pages.shape[:-1], rope_dim, dtype=dtype)
    pages[order] = key.reshape_as(pages)
    rope_pages[order] = rope.reshape_as(rope_pages)
    indices = torch.full((3, 1, sparse_capacity), -1, dtype=torch.int32)
    for row, visible in enumerate((255 if mode == 3 else 256, 256, 1024)):
        block_count = (visible + sparse_block_size - 1) // sparse_block_size
        count = 0 if row == 0 else min(sparse_capacity, block_count)
        # Keep the valid prefix in reverse logical order, with random physical
        # pages, so block expansion cannot rely on ascending token positions.
        selected = torch.randperm(block_count)[:count].sort(descending=True).values
        indices[row, 0, :count] = selected.int()
    inputs = dict(
        query=query.npu(),
        key=pages.npu(),
        query_rope=query_rope.npu(),
        key_rope=rope_pages.npu(),
        sparse_indices=indices.npu(),
        block_table=table.npu(),
        actual_seq_lengths_query=torch.tensor(query_lengths, dtype=torch.int32).cumsum(0).int().npu(),
        actual_seq_lengths_kv=torch.tensor(kv_lengths, dtype=torch.int32).npu(),
        scale_value=1 / 24,
        sparse_block_size=sparse_block_size,
        sparse_mode=mode,
        attention_mode=2,
        layout_query="TND",
        layout_kv="PA_BSND",
        return_softmax_lse=True,
    )
    inputs["value"] = inputs["key"]
    cpu = dict(
        query=query,
        query_rope=query_rope,
        key=key,
        rope=rope,
        indices=indices,
        table=table,
        pages=pages,
        rope_pages=rope_pages,
    )
    return inputs, cpu


def check_outputs(outputs, cpu, sparse_block_size, mode):
    output, maximum, total = [x.cpu().double() for x in outputs]
    lse = (maximum + total.log()).squeeze(0)
    for row, (batch, visible) in enumerate(((0, 255 if mode == 3 else 256), (0, 256), (1, 1024))):
        selected_blocks = cpu["indices"][row, 0]
        selected_blocks = selected_blocks[selected_blocks >= 0].long()
        selected = (selected_blocks[:, None] * sparse_block_size + torch.arange(sparse_block_size)).flatten()
        selected = selected[selected < visible]
        if not selected.numel():
            continue  # Preserve the pre-existing empty-row behavior separately.
        logits = cpu["query"][row].double() @ cpu["key"][batch, selected, 0].double().T
        logits += cpu["query_rope"][row].double() @ cpu["rope"][batch, selected, 0].double().T
        logits /= 24
        expected = logits.softmax(-1) @ cpu["key"][batch, selected, 0].double()
        torch.testing.assert_close(output[row], expected, atol=0.03, rtol=0.01)
        torch.testing.assert_close(lse[row], logits.logsumexp(-1), atol=0.005, rtol=0.001)


@pytest.mark.parametrize("page_size", [48, 64, 128])
@pytest.mark.parametrize("dtype", [torch.float16, torch.bfloat16])
@pytest.mark.parametrize("sparse_capacity", [1, 3, 17, 257, 513])
@pytest.mark.parametrize("sparse_block_size", [1, 2, 4])
@pytest.mark.parametrize("mode", [0, 3])
@torch.inference_mode()
def test_sparse_index_traversal(dtype, sparse_capacity, sparse_block_size, mode, page_size):
    assert enable_custom_op()
    inputs, cpu = make_inputs(dtype, sparse_capacity, sparse_block_size, mode, page_size)
    outputs = torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
    check_outputs(outputs, cpu, sparse_block_size, mode)


@pytest.mark.parametrize("page_size", [48, 64, 128])
@pytest.mark.parametrize("dtype", [torch.float16, torch.bfloat16])
@pytest.mark.parametrize("sparse_block_size", [1, 2, 4])
@torch.inference_mode()
def test_sparse_index_graph_reloads_inputs(dtype, sparse_block_size, page_size):
    assert enable_custom_op()
    inputs, cpu = make_inputs(dtype, 513, sparse_block_size, 0, page_size)
    for _ in range(3):
        torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    with torch.npu.graph(graph):
        outputs = torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
    for count, swap_pages in ((1, False), (17, True), (513, False)):
        changed = cpu["indices"].clone()
        changed[..., count:] = -1
        inputs["sparse_indices"].copy_(changed.npu())
        changed_table = cpu["table"].flip(-1) if swap_pages else cpu["table"]
        inputs["block_table"].copy_(changed_table.npu())
        changed_key = cpu["pages"][changed_table.long()].reshape_as(cpu["key"])
        changed_rope = cpu["rope_pages"][changed_table.long()].reshape_as(cpu["rope"])
        graph.replay()
        torch.npu.synchronize()
        check_outputs(
            outputs, {**cpu, "indices": changed, "key": changed_key, "rope": changed_rope}, sparse_block_size, 0
        )
