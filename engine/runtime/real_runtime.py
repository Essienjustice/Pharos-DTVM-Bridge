from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any


def _failure(stage: str, error: str, stdout: str = "", stderr: str = "") -> dict[str, Any]:
    return {
        "status": "FAILURE",
        "stage": stage,
        "error": error,
        "stdout": stdout,
        "stderr": stderr,
    }


@dataclass(frozen=True)
class RealRuntime:
    rpc_url: str | None = None
    wallet_address: str | None = None

    def _run(self, command: list[str], timeout: int) -> dict[str, Any]:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            return _failure("subprocess", f"Missing executable: {command[0]}", stderr=str(exc))
        except subprocess.TimeoutExpired as exc:
            return _failure("subprocess", f"Command timed out after {timeout}s", stdout=exc.stdout or "", stderr=exc.stderr or "")

        result = {
            "status": "SUCCESS" if completed.returncode == 0 else "FAILURE",
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "command": command,
        }
        if completed.returncode != 0:
            result["error"] = completed.stderr.strip() or completed.stdout.strip() or "Subprocess failed."
        return result

    def _rpc(self) -> str:
        return self.rpc_url or "https://atlantic.dplabs-internal.com"

    def validate_balance(self) -> dict[str, Any]:
        if not self.wallet_address:
            return _failure("balance", "Missing wallet address for deployment")
        result = self._run(["cast", "balance", self.wallet_address, "--rpc-url", self._rpc()], timeout=60)
        if result["status"] != "SUCCESS":
            return result
        try:
            balance = int(str(result["stdout"]).strip() or "0")
        except ValueError:
            return _failure("balance", "Unable to parse wallet balance", stdout=str(result["stdout"]))
        if balance == 0:
            return _failure("balance", "Insufficient balance for deployment", stdout=str(result["stdout"]))
        return {"status": "SUCCESS", "balance": balance}

    def deploy_wasm_command(self, contract_path: str) -> list[str]:
        return ["cargo", "stylus", "deploy", "--manifest-path", contract_path]

    def deploy_evm_command(self, contract_name: str) -> list[str]:
        return ["forge", "create", contract_name, "--rpc-url", self._rpc()]

    def call_command(self, target: str, signature: str) -> list[str]:
        return ["cast", "call", target, signature, "--rpc-url", self._rpc()]

    def trace_command(self, tx_hash: str) -> list[str]:
        return ["cast", "rpc", "debug_traceTransaction", tx_hash, "--rpc-url", self._rpc()]

    def deploy_wasm(self, contract_name: str) -> dict[str, Any]:
        balance = self.validate_balance()
        if balance["status"] != "SUCCESS":
            return balance
        deploy = self._run(self.deploy_wasm_command(contract_name), timeout=120)
        if deploy["status"] != "SUCCESS":
            return deploy
        wasm_address = self._extract_address(str(deploy["stdout"]))
        if not wasm_address:
            return _failure("deploy_wasm", "Unable to extract WASM address", stdout=str(deploy["stdout"]), stderr=str(deploy["stderr"]))
        code = self._run(["cast", "code", wasm_address, "--rpc-url", self._rpc()], timeout=60)
        if code["status"] != "SUCCESS":
            return code
        if str(code["stdout"]).strip() == "0x":
            return _failure("deploy_wasm", "WASM deployment produced no bytecode", stdout=str(code["stdout"]))
        return {"status": "SUCCESS", "wasm_address": wasm_address, "deploy_output": deploy, "code": code["stdout"]}

    def deploy_evm(self, contract_name: str, wasm_address: str) -> dict[str, Any]:
        balance = self.validate_balance()
        if balance["status"] != "SUCCESS":
            return balance
        deploy = self._run(self.deploy_evm_command(contract_name), timeout=60)
        if deploy["status"] != "SUCCESS":
            return deploy
        evm_address = self._extract_address(str(deploy["stdout"]))
        if not evm_address:
            return _failure("deploy_evm", "Unable to extract EVM address", stdout=str(deploy["stdout"]), stderr=str(deploy["stderr"]))
        dry_run = self._run(
            ["cast", "call", evm_address, "wasmBalanceOf(address)(uint256)", evm_address, "--rpc-url", self._rpc()],
            timeout=60,
        )
        return {
            "status": "SUCCESS",
            "evm_address": evm_address,
            "wasm_address": wasm_address,
            "deploy_output": deploy,
            "dry_run_output": dry_run,
        }

    def call_cross_vm(self, evm_address: str, function: str, value: int = 100) -> dict[str, object]:
        return self._run(self.call_command(evm_address, function), timeout=60)

    def trace(self, tx_hash: str) -> dict[str, object]:
        return self._run(self.trace_command(tx_hash), timeout=60)

    @staticmethod
    def _extract_address(output: str) -> str | None:
        for token in output.replace("\n", " ").split():
            stripped = token.strip(",:;")
            if stripped.startswith("0x") and len(stripped) == 42:
                return stripped
        return None
