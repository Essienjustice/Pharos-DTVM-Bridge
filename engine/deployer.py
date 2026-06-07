from __future__ import annotations

from .mock_runtime import MockRuntime
from .schema import DeploymentResult, GeneratedArtifacts, ValidationReport


CHAIN_IDS = {
    "testnet": 688689,
    "mainnet": 1672,
}


def deploy_artifacts(
    artifacts: GeneratedArtifacts,
    validation: ValidationReport,
    runtime: MockRuntime,
    network: str,
) -> DeploymentResult:
    if validation.status != "SUCCESS":
        return DeploymentResult(
            status="FAILURE",
            network=network,
            chain_id=CHAIN_IDS.get(network, 0),
            wasm_address="",
            evm_address="",
            deploy_tx_wasm="",
            deploy_tx_evm="",
            errors=["Validation failed; deployment skipped.", *validation.errors],
        )

    wasm_address, wasm_tx = runtime.deploy_wasm(artifacts.wasm_contract["contract_name"])
    evm_address, evm_tx, failure = runtime.deploy_evm(
        artifacts.evm_contract["contract_name"],
        wasm_address,
    )

    if failure is not None:
        return DeploymentResult(
            status="FAILURE",
            network=network,
            chain_id=CHAIN_IDS.get(network, 0),
            wasm_address=wasm_address,
            evm_address="",
            deploy_tx_wasm=wasm_tx,
            deploy_tx_evm="",
            errors=[failure["explanation"]],
            failure=failure,
        )

    return DeploymentResult(
        status="SUCCESS",
        network=network,
        chain_id=CHAIN_IDS.get(network, 0),
        wasm_address=wasm_address,
        evm_address=evm_address,
        deploy_tx_wasm=wasm_tx,
        deploy_tx_evm=evm_tx,
    )
