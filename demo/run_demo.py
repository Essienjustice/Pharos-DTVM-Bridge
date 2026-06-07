from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import AgentRequest, run_pipeline


def divider(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def run_case(title: str, simulation_mode: str) -> dict[str, object]:
    divider(f"=== {title} ===")
    request = AgentRequest.from_intent(
        "Write a Solidity contract that calls a Rust mint function",
        network="testnet",
        simulation_mode=simulation_mode,
    )
    result = run_pipeline(request)
    print("Pipeline logs")
    print("-" * 72)
    for line in result["logs"]:
        print(line)
    print()
    print("JSON output")
    print("-" * 72)
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    success = run_case("SUCCESS CASE", "success")
    failure = run_case("FAILURE CASE: ABI MISMATCH", "abi_mismatch")
    return 0 if success["status"] == "SUCCESS" and failure["status"] == "FAILURE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
