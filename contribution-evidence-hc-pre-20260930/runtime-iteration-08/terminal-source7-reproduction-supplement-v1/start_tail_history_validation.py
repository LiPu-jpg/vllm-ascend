"""Start once in a freshly guarded window; never restart from an observation timeout."""

import hashlib
import json
import subprocess
from pathlib import Path


def main():
    root = Path("/mnt/workspace/hc-pre-reduction-20260930")
    iteration = root / "iteration-08"
    assert (iteration / "controller-v3-hf32-reference.exit").read_text().strip() == "0"
    assert (
        "ALL6_HF32_MIDPOINT_HARDWARE_REGRESSIONS_PASS_PER_ARM"
        in (iteration / "controller-v3-hf32-reference.log").read_text()
    )
    for suffix in ("pid", "exit", "log"):
        assert not (iteration / f"controller-v3c-tail-history.{suffix}").exists(), (
            suffix
        )
    for record in root.glob("iteration-*/controller*.pid"):
        try:
            words = (
                Path("/proc") / record.read_text().strip() / "cmdline"
            ).read_bytes()
        except FileNotFoundError:
            continue
        assert str(root).encode() not in words, f"Own controller still live: {record}"
    for manifest in (
        "frozen-input-sha256.json",
        "validation-input-sha256.json",
        "hf32-reference-input-sha256.json",
        "tail-history-input-sha256.json",
    ):
        for name, expected in json.loads((iteration / manifest).read_text()).items():
            assert (
                hashlib.sha256((iteration / name).read_bytes()).hexdigest() == expected
            ), name
    subprocess.run(
        ["python3", str(iteration / "verify_shared_validation_dependencies.py")],
        check=True,
    )
    subprocess.run(["python3", str(iteration / "foreign_jobs.py")], check=True)
    with (iteration / "controller-v3c-tail-history.log").open("xb") as log:
        child = subprocess.Popen(
            ["bash", str(iteration / "controller_tail_history.sh")],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print("STARTED_PID", child.pid, flush=True)


if __name__ == "__main__":
    main()
