from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

from pharos_config import envelope, get_network


ROOT = Path(__file__).resolve().parents[1]
WASM_DIR = ROOT / "contracts" / "wasm-counter"
DEPLOYMENTS_DIR = ROOT / "deployments"
ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")
TX_RE = re.compile(r"0x[a-fA-F0-9]{64}")


def run(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)


def first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy the Pharos DTVM counter pair.")
    parser.add_argument("--network", choices=["testnet", "mainnet"], default=None)
    parser.add_argument("--private-key", default=None)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    network = get_network(args.network)
    private_key = args.private_key or os.getenv("PRIVATE_KEY")

    errors: list[str] = []
    artifacts: dict[str, object] = {
        "wasm_contract": {
            "filename": "contracts/wasm-counter/src/lib.rs",
            "language": "rust",
            "framework": "stylus-sdk",
            "compile_cmd": f"cargo stylus check --endpoint={network.rpc}",
        },
        "evm_contract": {
            "filename": "contracts/evm/CrossVmCounterCaller.sol",
            "language": "solidity",
            "solc_version": "^0.8.20",
            "compile_cmd": "forge build",
        },
        "deployment": {"deploy_order": "WASM_FIRST"},
    }

    if not private_key or private_key.endswith("0000000000000000000000000000000000000000"):
        errors.append("Set PRIVATE_KEY in .env or pass --private-key.")
        print(json.dumps(envelope("DEPLOY", network, "FAILURE", artifacts=artifacts, errors=errors), indent=2))
        return 1

    w3 = Web3(Web3.HTTPProvider(network.rpc))
    account = Account.from_key(private_key)
    balance = w3.eth.get_balance(account.address)
    if balance == 0:
        errors.append(f"Wallet {account.address} has zero {network.native}.")
        print(json.dumps(envelope("DEPLOY", network, "FAILURE", artifacts=artifacts, errors=errors), indent=2))
        return 1

    try:
        run(["cargo", "stylus", "check", f"--endpoint={network.rpc}"], WASM_DIR)
        wasm_deploy = run(
            ["cargo", "stylus", "deploy", f"--private-key={private_key}", f"--endpoint={network.rpc}"],
            WASM_DIR,
        )
        wasm_output = wasm_deploy.stdout + "\n" + wasm_deploy.stderr
        wasm_address = first_match(ADDRESS_RE, wasm_output)
        wasm_tx = first_match(TX_RE, wasm_output)
        if wasm_address is None:
            raise RuntimeError("cargo stylus deploy did not print a contract address.")

        code = w3.eth.get_code(Web3.to_checksum_address(wasm_address))
        if not code:
            raise RuntimeError(f"No code found at deployed WASM address {wasm_address}.")

        evm_deploy = run(
            [
                "forge",
                "create",
                "contracts/evm/CrossVmCounterCaller.sol:CrossVmCounterCaller",
                "--constructor-args",
                wasm_address,
                "--private-key",
                private_key,
                "--rpc-url",
                network.rpc,
            ]
        )
        evm_output = evm_deploy.stdout + "\n" + evm_deploy.stderr
        addresses = ADDRESS_RE.findall(evm_output)
        txs = TX_RE.findall(evm_output)
        evm_address = addresses[-1] if addresses else None
        evm_tx = txs[-1] if txs else None
        if evm_address is None:
            raise RuntimeError("forge create did not print a deployed EVM address.")

        dry_run = run(
            [
                "cast",
                "call",
                evm_address,
                "readWasmCounter()(uint256)",
                "--rpc-url",
                network.rpc,
            ]
        )

        artifacts["deployment"] = {
            "wasm_address": wasm_address,
            "evm_address": evm_address,
            "deploy_tx_wasm": wasm_tx,
            "deploy_tx_evm": evm_tx,
            "deploy_order": "WASM_FIRST",
            "explorer_wasm": f"{network.explorer}/address/{wasm_address}",
            "explorer_evm": f"{network.explorer}/address/{evm_address}",
            "dry_run_output": dry_run.stdout.strip(),
        }

        DEPLOYMENTS_DIR.mkdir(exist_ok=True)
        deployment_file = DEPLOYMENTS_DIR / f"{network.name}.json"
        deployment_file.write_text(json.dumps(artifacts["deployment"], indent=2) + "\n", encoding="utf-8")

        print(json.dumps(envelope("DEPLOY", network, "SUCCESS", artifacts=artifacts), indent=2))
        return 0
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        detail = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            detail = (exc.stdout or "") + "\n" + (exc.stderr or "")
        errors.append(detail.strip())
        print(json.dumps(envelope("DEPLOY", network, "FAILURE", artifacts=artifacts, errors=errors), indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
