from __future__ import annotations

import argparse
import json

from engine import AgentRequest, run_pipeline
from presentation import print_progressive_logs
from presentation_config import DEFAULT_PRESENTATION_DELAY


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Pharos DTVM cross-VM agent pipeline.")
    parser.add_argument("intent", help="Natural language cross-VM contract request")
    parser.add_argument("--network", default="testnet", choices=["testnet", "mainnet"])
    parser.add_argument(
        "--simulate",
        default="success",
        choices=["success", "abi_mismatch", "wasm_revert", "deploy_order_error", "gas_exhaustion"],
        help="Deterministic mock runtime scenario to execute.",
    )
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

    request = AgentRequest.from_intent(
        args.intent,
        network=args.network,
        simulation_mode=args.simulate,
    )
    result = run_pipeline(request)
    if args.presentation:
        print_progressive_logs(
            result["logs"],
            presentation=args.presentation,
            delay=args.presentation_delay,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
