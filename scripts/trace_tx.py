from __future__ import annotations

import argparse
import json

from dotenv import load_dotenv
from web3 import Web3

from pharos_config import envelope, get_network


def walk_calls(frame: dict[str, object]) -> list[dict[str, object]]:
    frames = [frame]
    for child in frame.get("calls", []) or []:
        if isinstance(child, dict):
            frames.extend(walk_calls(child))
    return frames


def classify(receipt: dict[str, object], trace: dict[str, object]) -> tuple[str | None, str | None]:
    frames = walk_calls(trace) if trace else []
    failed = receipt.get("status") == 0

    if not failed:
        return None, None
    if not frames:
        return "EVM_REVERT", "Transaction failed and no call trace frames were returned."
    if len(frames) == 1:
        return "EVM_REVERT", "Top-level frame reverted before a nested cross-VM call was visible."

    nested = frames[1:]
    empty_output = [f for f in nested if f.get("output") in (None, "0x", "")]
    errors = [f for f in nested if f.get("error")]
    gas_like = [f for f in frames if "gas" in str(f.get("error", "")).lower()]

    if gas_like:
        return "GAS", "Trace includes a gas-related failure."
    if errors:
        return "WASM_REVERT", f"Nested call reverted: {errors[0].get('error')}"
    if empty_output:
        return "ABI_MISMATCH", "Nested call reached a target but returned no output."
    return "SILENT", "Receipt failed but trace did not expose a specific revert reason."


def main() -> int:
    parser = argparse.ArgumentParser(description="Trace and classify a Pharos cross-VM transaction.")
    parser.add_argument("--network", choices=["testnet", "mainnet"], default=None)
    parser.add_argument("--tx", required=True, help="Transaction hash")
    args = parser.parse_args()

    load_dotenv()
    network = get_network(args.network)
    w3 = Web3(Web3.HTTPProvider(network.rpc))
    errors: list[str] = []

    try:
        receipt = w3.eth.get_transaction_receipt(args.tx)
        trace = w3.provider.make_request(
            "debug_traceTransaction",
            [args.tx, {"tracer": "callTracer"}],
        )
        if "error" in trace:
            raise RuntimeError(trace["error"])
        call_tree = trace.get("result", {})
        failure_class, failure_detail = classify(dict(receipt), call_tree)

        payload = envelope(
            "TRACE",
            network,
            "SUCCESS",
            trace={
                "tx_hash": args.tx,
                "call_tree": call_tree,
                "cross_vm_boundary_detected": len(walk_calls(call_tree)) > 1 if call_tree else False,
                "failure_class": failure_class,
                "failure_detail": failure_detail,
            },
            next_steps=[
                "Compare nested call input selectors with scripts/check_selectors.py",
                "Verify WASM was deployed before the EVM caller",
            ],
        )
        print(json.dumps(payload, indent=2, default=str))
        return 0
    except Exception as exc:
        errors.append(str(exc))
        print(json.dumps(envelope("TRACE", network, "FAILURE", errors=errors), indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
