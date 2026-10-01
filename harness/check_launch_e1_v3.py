import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--results", type=Path, required=True)
a = p.parse_args()
records = []
for variant in ["control", "candidate"]:
    profile = json.loads((a.results / f"profile-{variant}.json").read_text())
    assert profile["complete"] and profile["all_passed"] and len(profile["rows"]) == 32
    for row in profile["rows"]:
        q = int(row["case"].rsplit("-", 1)[1])
        expected = min(q, 20) if variant == "candidate" else 20
        kernels = row["profile"]["kernel_rows"]
        assert len(kernels) == 5
        assert all(
            int(k["Block Num"]) == expected and int(k["Mix Block Num"]) == 2 * expected
            for k in kernels
        ), (variant, row["case"], kernels)
        records.append(
            dict(
                variant=variant,
                case=row["case"],
                order=row["order"],
                return_lse=row["return_lse"],
                aic=expected,
                aiv=2 * expected,
            )
        )
(a.results / "actual-launch-gate.json").write_text(
    json.dumps(dict(passed=True, records=records), indent=2) + "\n"
)
print("64 profile records prove original20/40, candidateq1=1/2 and q32=20/40")
