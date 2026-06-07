from __future__ import annotations

from dataclasses import dataclass, field


def _address(seed: int) -> str:
    return "0x" + f"{seed:040x}"[-40:]


def _tx(seed: int) -> str:
    return "0x" + f"{seed:064x}"[-64:]


@dataclass
class MockRuntime:
    simulation_mode: str = "success"
    next_id: int = 1
    wasm_state: dict[str, dict[str, int]] = field(default_factory=dict)
    evm_targets: dict[str, str] = field(default_factory=dict)

    def failure(self, error_type: str, failed_stage: str, explanation: str) -> dict[str, str]:
        return {
            "error_type": error_type,
            "failed_stage": failed_stage,
            "explanation": explanation,
        }

    def deploy_wasm(self, contract_name: str) -> tuple[str, str]:
        address = _address(self.next_id)
        tx_hash = _tx(self.next_id)
        self.next_id += 1
        self.wasm_state[address] = {"minted": 0, "counter": 0}
        return address, tx_hash

    def deploy_evm(self, contract_name: str, wasm_address: str) -> tuple[str, str, dict[str, str] | None]:
        if self.simulation_mode == "deploy_order_error":
            failure = self.failure(
                "DEPLOY_ORDER_ERROR",
                "deployer",
                "EVM caller targets an address with no WASM bytecode. WASM must be deployed first.",
            )
            return "", "", failure

        address = _address(self.next_id)
        tx_hash = _tx(self.next_id)
        self.next_id += 1
        self.evm_targets[address] = wasm_address
        return address, tx_hash, None

    def call_cross_vm(self, evm_address: str, function: str, value: int = 100) -> dict[str, object]:
        wasm_address = self.evm_targets[evm_address]
        selector = function.split("(", 1)[0]
        evm_method = "mintViaWasm(uint256)" if selector == "mint" else "incrementViaWasm(uint256)"
        tx_hash = _tx(self.next_id)
        self.next_id += 1

        if self.simulation_mode == "abi_mismatch":
            failure = self.failure(
                "ABI_MISMATCH",
                "tracer",
                "EVM calldata selector did not match any exported WASM function selector.",
            )
            return {
                "tx_hash": tx_hash,
                "output_value": None,
                "failure": failure,
                "call_tree": {
                    "type": "CALL",
                    "from": _address(999),
                    "to": evm_address,
                    "input": evm_method,
                    "output": "0x",
                    "error": failure["error_type"],
                    "calls": [
                        {
                            "type": "CALL",
                            "from": evm_address,
                            "to": wasm_address,
                            "input": "0xdeadbeef",
                            "output": "0x",
                            "error": failure["error_type"],
                        }
                    ],
                },
            }

        if self.simulation_mode == "wasm_revert":
            failure = self.failure(
                "WASM_REVERT",
                "tracer",
                "WASM reverted: 'Insufficient balance' (Error(string), ABI-decoded)",
            )
            return {
                "tx_hash": tx_hash,
                "output_value": None,
                "failure": failure,
                "call_tree": {
                    "type": "CALL",
                    "from": _address(999),
                    "to": evm_address,
                    "input": evm_method,
                    "output": "0x",
                    "error": failure["error_type"],
                    "calls": [
                        {
                            "type": "CALL",
                            "from": evm_address,
                            "to": wasm_address,
                            "input": function,
                            "output": "0x08c379a0",
                            "error": failure["error_type"],
                            "decoded_error": "Insufficient balance",
                        }
                    ],
                },
            }

        if self.simulation_mode == "gas_exhaustion":
            failure = self.failure(
                "GAS_EXHAUSTION",
                "tracer",
                "Transaction gas_used equals gas_limit. Cross-VM calls cost more gas than same-VM calls. Increase gas limit.",
            )
            return {
                "tx_hash": tx_hash,
                "output_value": None,
                "failure": failure,
                "call_tree": {
                    "type": "CALL",
                    "from": _address(999),
                    "to": evm_address,
                    "input": evm_method,
                    "output": "0x",
                    "error": failure["error_type"],
                    "gas_used": 500000,
                    "gas_limit": 500000,
                    "calls": [
                        {
                            "type": "CALL",
                            "from": evm_address,
                            "to": wasm_address,
                            "input": function,
                            "output": "0x",
                            "error": failure["error_type"],
                        }
                    ],
                },
            }

        state = self.wasm_state[wasm_address]

        if selector == "mint":
            state["minted"] += value
            output_value = state["minted"]
        elif selector == "increment":
            state["counter"] += value
            output_value = state["counter"]
        else:
            output_value = 0
            evm_method = selector

        return {
            "tx_hash": tx_hash,
            "output_value": output_value,
            "failure": None,
            "call_tree": {
                "type": "CALL",
                "from": _address(999),
                "to": evm_address,
                "input": evm_method,
                "output": hex(output_value),
                "calls": [
                    {
                        "type": "CALL",
                        "from": evm_address,
                        "to": wasm_address,
                        "input": function,
                        "output": hex(output_value),
                    }
                ],
            },
        }
