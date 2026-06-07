from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import AgentRequest, run_pipeline
from presentation import print_progressive_logs
from presentation_config import DEFAULT_PRESENTATION_DELAY


def divider(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def run_case(
    title: str,
    simulation_mode: str,
    *,
    presentation: bool,
    presentation_delay: float,
) -> dict[str, object]:
    divider(f"=== {title} ===")
    request = AgentRequest.from_intent(
        "Write a Solidity contract that calls a Rust mint function",
        network="testnet",
        simulation_mode=simulation_mode,
    )
    result = run_pipeline(request)
    print("Pipeline logs")
    print("-" * 72)
    print_progressive_logs(
        result["logs"],
        presentation=presentation,
        delay=presentation_delay,
    )
    print()
    print("JSON output")
    print("-" * 72)
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the pharos-dtvm-bridge demo.")
    parser.add_argument(
        "--presentation",
        action="store_true",
        help="Print pipeline logs progressively for demos and video recording.",
    )
    parser.add_argument(
        "--presentation-delay",
        type=float,
        default=DEFAULT_PRESENTATION_DELAY,
        help="Delay in seconds between log lines when --presentation is enabled.",
    )
    args = parser.parse_args()

    cases = [
        ("SUCCESS CASE", "success", "SUCCESS"),
        ("FAILURE CASE: ABI MISMATCH", "abi_mismatch", "FAILURE"),
    ]
    if args.presentation:
        cases.extend(
            [
                ("FAILURE CASE: WASM REVERT", "wasm_revert", "FAILURE"),
                ("FAILURE CASE: DEPLOY ORDER ERROR", "deploy_order_error", "FAILURE"),
            ]
        )

    results = [
        run_case(
            title,
            simulation_mode,
            presentation=args.presentation,
            presentation_delay=args.presentation_delay,
        )
        for title, simulation_mode, _expected_status in cases
    ]

    return 0 if all(result["status"] == expected for result, (*_, expected) in zip(results, cases)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
