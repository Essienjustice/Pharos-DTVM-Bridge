from __future__ import annotations

from typing import Any

from .compiler import compile_artifacts
from .deployer import deploy_artifacts
from .generator import generate_artifacts
from .mock_runtime import MockRuntime
from .planner import create_plan
from .schema import AgentRequest, to_jsonable
from .tracer import trace_cross_vm_call
from .validator import validate_artifacts


DTVM_REFERENCE = {
    "paper": "https://arxiv.org/abs/2504.16552",
    "source": "https://github.com/PharosNetwork/DTVM",
    "engine": "ZetaEngine (Lazy-JIT, LLVM 15)",
    "ir_layer": "dMIR (Deterministic Middle Intermediate Representation)",
}


def run_pipeline(request: AgentRequest) -> dict[str, Any]:
    logs: list[str] = []
    runtime = MockRuntime(simulation_mode=request.simulation_mode)

    try:
        logs.append("[PLAN] Planner started")
        plan = create_plan(request)
        logs.append(f"[PLAN] Cross-VM intent detected: {plan.direction}")
        logs.append("[SPEC] Spec builder completed")
        logs.append(f"[SPEC] Archetype classified: {plan.application_type}")

        logs.append("[GENERATOR] Generator started")
        artifacts = generate_artifacts(plan)
        logs.append(
            "[GENERATOR] Solidity + Rust contracts generated "
            f"({artifacts.evm_contract['contract_name']} -> {artifacts.wasm_contract['contract_name']})"
        )

        logs.append("[VALIDATOR] Validator started")
        validation = validate_artifacts(plan, artifacts)
        if validation.status == "SUCCESS":
            logs.append("[VALIDATOR] ABI compatibility OK")
        else:
            logs.append(f"[VALIDATOR] ABI compatibility FAILED: {'; '.join(validation.errors)}")

        logs.append("[COMPILER] Mock compiler started")
        compilation = compile_artifacts(artifacts, mode="mock")
        if compilation.success:
            logs.append("[COMPILER] Mock syntax validation OK")
        else:
            logs.append(f"[COMPILER] Mock syntax validation FAILED: {'; '.join(compilation.errors)}")

        logs.append("[DEPLOYER] Deploy order: WASM_FIRST")
        if compilation.success:
            deployment = deploy_artifacts(artifacts, validation, runtime, request.network)
        else:
            from .schema import DeploymentResult

            deployment = DeploymentResult(
                status="FAILURE",
                network=request.network,
                chain_id=0,
                wasm_address="",
                evm_address="",
                deploy_tx_wasm="",
                deploy_tx_evm="",
                errors=["Compilation failed; deployment skipped.", *compilation.errors],
            )
        if deployment.wasm_address:
            logs.append(f"[DEPLOYER] WASM deployed -> {deployment.wasm_address}")
        if deployment.evm_address:
            logs.append(f"[DEPLOYER] EVM deployed -> {deployment.evm_address}")
        if deployment.status != "SUCCESS":
            detail = deployment.errors[0] if deployment.errors else "deployment failed"
            logs.append(f"[DEPLOYER] Deployment FAILED: {detail}")

        logs.append("[TRACER] Tracer started")
        trace = trace_cross_vm_call(plan, validation, deployment, runtime)
        if trace.status == "SUCCESS":
            logs.append("[TRACER] Cross-VM execution SUCCESS")
        else:
            logs.append(f"[TRACER] Cross-VM execution FAILED: {trace.failure_class} - {trace.failure_detail}")
    except Exception as exc:
        logs.append(f"[PIPELINE] Structured failure: {type(exc).__name__}: {exc}")
        return {
            "skill": "pharos-dtvm-bridge",
            "version": "1.0.0",
            "status": "FAILURE",
            "runtime": "mock",
            "simulation_mode": request.simulation_mode,
            "logs": logs,
            "request": to_jsonable(request),
            "dtvm_reference": DTVM_REFERENCE,
            "failure_class": "PIPELINE_ERROR",
            "detail": f"{type(exc).__name__}: {exc}",
            "errors": [f"{type(exc).__name__}: {exc}"],
        }

    status = "SUCCESS"
    errors: list[str] = []
    if validation.errors:
        status = "FAILURE"
        errors.extend(validation.errors)
    if compilation.errors:
        status = "FAILURE"
        errors.extend(compilation.errors)
    if deployment.errors:
        status = "FAILURE"
        errors.extend(deployment.errors)
    if trace.failure_detail:
        status = "FAILURE"
        if trace.failure_detail not in errors:
            errors.append(trace.failure_detail)

    return {
        "skill": "pharos-dtvm-bridge",
        "version": "1.0.0",
        "action": plan.action,
        "network": request.network,
        "chain_id": deployment.chain_id,
        "status": status,
        "application_type": plan.application_type,
        "contracts": {
            "wasm": plan.wasm_contract,
            "evm": plan.evm_contract,
        },
        "runtime": "mock",
        "simulation_mode": request.simulation_mode,
        "dtvm_reference": DTVM_REFERENCE,
        "failure_class": trace.failure_class,
        "detail": trace.detail,
        "logs": logs,
        "request": to_jsonable(request),
        "spec": to_jsonable(plan.spec),
        "plan": to_jsonable(plan),
        "artifacts": to_jsonable(artifacts),
        "validation": to_jsonable(validation),
        "compilation": {
            "mode": compilation.mode,
            "cargo_check": compilation.artifacts.get("cargo_check", ""),
            "forge_build": compilation.artifacts.get("forge_build", ""),
            "selector_validation": "PASSED" if validation.status == "SUCCESS" else "FAILED",
        },
        "deployment": to_jsonable(deployment),
        "trace": to_jsonable(trace),
        "errors": errors,
        "next_steps": [
            "Install Foundry to run forge build and forge test.",
            "Use scripts/deploy.py only when ready for a real Pharos RPC deployment.",
        ],
    }
