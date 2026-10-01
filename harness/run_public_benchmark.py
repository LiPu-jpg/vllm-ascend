"""Run the public benchmark with private window checks outside timed events."""

import argparse
import importlib.util
import sys
from pathlib import Path
from experiment import guard

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--variant", choices=["baseline", "candidate"], required=True)
_, remaining = parser.parse_known_args()
path = Path(__file__).with_name("benchmark_sparse_flash_attention_small_query.py")
spec = importlib.util.spec_from_file_location("public_benchmark", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original_run = module.run
original_event = module.torch.npu.Event


def checked_run(*args, **kwargs):
    guard()
    return original_run(*args, **kwargs)


def checked_event(*args, **kwargs):
    guard()
    return original_event(*args, **kwargs)


module.run = checked_run
module.torch.npu.Event = checked_event
sys.argv = [str(path), *remaining]
guard()
module.main()
guard()
