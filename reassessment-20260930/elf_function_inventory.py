"""Compare ELF64 function sizes/bytes; differences do not establish a cause."""

import argparse
import hashlib
import json
import struct
from pathlib import Path


def functions(path):
    data = path.read_bytes()
    assert data[:6] == b"\x7fELF\x02\x01", "Expected little-endian ELF64"
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", data)
    sections = [
        struct.unpack_from("<IIQQQQIIQQ", data, header[6] + i * header[11])
        for i in range(header[12])
    ]
    result = {}
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        strings_section = sections[section[6]]
        strings = data[strings_section[4] : strings_section[4] + strings_section[5]]
        for offset in range(section[4], section[4] + section[5], section[9]):
            name, info, _, index, value, size = struct.unpack_from("<IBBHQQ", data, offset)
            if info & 15 != 2 or index == 0 or index >= len(sections):
                continue
            symbol = strings[name:].split(b"\0", 1)[0].decode()
            segment = sections[index]
            start = segment[4] + value - segment[3]
            code = data[start : start + size]
            assert len(code) == size
            result[symbol] = {"size": size, "sha256": hashlib.sha256(code).hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    records = []
    for baseline in sorted(args.baseline.glob("*.o")):
        candidate = args.candidate / baseline.name
        before, after = functions(baseline), functions(candidate)
        assert before.keys() == after.keys()
        records.append(
            {
                "object": baseline.name,
                "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
                "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                "functions": [
                    {"symbol": name, "baseline": before[name], "candidate": after[name]}
                    for name in before
                ],
            }
        )
    assert len(records) == 2
    args.output.write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
