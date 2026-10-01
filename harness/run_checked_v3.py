"""Run a private probe and verify the process loaded this runtime's host tiling."""

import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-runtime", type=Path, required=True)
    parser.add_argument("--program", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args, remaining = parser.parse_known_args()
    assert not args.record.exists()
    expected = args.expected_runtime.resolve()
    sys.path.insert(0, str(args.program.parent))
    sys.argv = [str(args.program), *remaining]
    status = 0
    error = None
    try:
        runpy.run_path(str(args.program), run_name="__main__")
    except SystemExit as exc:
        status = exc.code if isinstance(exc.code, int) else int(bool(exc.code))
    except Exception as exc:
        status = 1
        error = repr(exc)
        raise
    finally:
        libraries = set()
        for line in Path("/proc/self/maps").read_text().splitlines():
            parts = line.split(maxsplit=5)
            if len(parts) != 6:
                continue
            path = Path(parts[-1])
            if path.is_file() and (
                path.is_relative_to(expected) or path.name == "liboptiling.so"
            ):
                libraries.add(path.resolve())
        host = (
            expected
            / "vllm_ascend/_cann_ops_custom/vendors/custom_transformer/op_impl/ai_core/tbe/op_tiling/liboptiling.so"
        )
        host = host.resolve()
        record = dict(
            program=str(args.program),
            status=status,
            error=error,
            expected_runtime=str(expected),
            expected_host_tiling=str(host),
            expected_host_tiling_loaded=host in libraries,
            loaded_libraries={
                str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(libraries)
            },
        )
        args.record.write_text(json.dumps(record, indent=2) + "\n")
    if status == 0:
        assert host in libraries, (
            "Expected private host tiling library was not loaded; reject this run."
        )
    raise SystemExit(status)


if __name__ == "__main__":
    main()
