from __future__ import annotations

from typing import Protocol


class Runtime(Protocol):
    def deploy_wasm(self, contract_name: str) -> tuple[str, str]:
        ...

    def deploy_evm(self, contract_name: str, wasm_address: str) -> tuple[str, str, dict[str, str] | None]:
        ...

    def call_cross_vm(self, evm_address: str, function: str, value: int = 100) -> dict[str, object]:
        ...

    def trace(self, tx_hash: str) -> dict[str, object]:
        ...
