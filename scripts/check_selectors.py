from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from eth_utils import keccak


@dataclass(frozen=True)
class Signature:
    name: str
    signature: str
    expected_selector: str


SIGNATURES = [
    Signature("increment", "increment(uint256)", "0x7cf5dab0"),
    Signature("get", "get()", "0x6d4ce63c"),
    Signature("setOwner", "setOwner(address)", "0x13af4035"),
]


def selector(signature: str) -> str:
    return "0x" + keccak(text=signature)[:4].hex()


def main() -> int:
    results = []
    errors = []

    for item in SIGNATURES:
        actual = selector(item.signature)
        ok = actual == item.expected_selector
        results.append({**asdict(item), "actual_selector": actual, "ok": ok})
        if not ok:
            errors.append(
                f"{item.signature}: expected {item.expected_selector}, computed {actual}"
            )

    print(
        json.dumps(
            {
                "skill": "pharos-dtvm-bridge",
                "version": "1.0.0",
                "action": "VALIDATE",
                "network": "none",
                "chain_id": None,
                "status": "SUCCESS" if not errors else "FAILURE",
                "artifacts": {
                    "abi_bridge": {
                        "interface_sol": "contracts/evm/interfaces/IWasmCounter.sol",
                        "sol_macro_rust": "contracts/wasm-counter/src/lib.rs",
                        "selectors": results,
                    }
                },
                "trace": {},
                "errors": errors,
                "next_steps": ["Run forge build", "Run cargo stylus check"],
            },
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
