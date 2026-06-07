from __future__ import annotations

import argparse
import json

from engine import AgentRequest, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Pharos DTVM cross-VM agent pipeline.")
    parser.add_argument("intent", help="Natural language cross-VM contract request")
    parser.add_argument("--network", default="testnet", choices=["testnet", "mainnet"])
    parser.add_argument(
        "--simulate",
        default="success",
        choices=["success", "abi_mismatch", "wasm_revert", "deploy_order_error"],
        help="Deterministic mock runtime scenario to execute.",
    )
    args = parser.parse_args()

    request = AgentRequest.from_intent(
        args.intent,
        network=args.network,
        simulation_mode=args.simulate,
    )
    result = run_pipeline(request)
    for line in result["logs"]:
        print(line)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
