from __future__ import annotations

from .generator import selector_for_signature
from .schema import GeneratedArtifacts, PlanOutput, ValidationReport


def validate_artifacts(plan: PlanOutput, artifacts: GeneratedArtifacts) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    selector_checks: list[dict[str, str | bool]] = []

    if not artifacts.wasm_contract.get("source"):
        errors.append("Missing Rust WASM source.")
    if not artifacts.evm_contract.get("source"):
        errors.append("Missing Solidity EVM source.")

    sol_source = artifacts.evm_contract.get("source", "")
    rust_source = artifacts.wasm_contract.get("source", "")

    bridge_selectors = {
        item["signature"]: item["selector"]
        for item in artifacts.abi_bridge.get("selectors", [])
        if isinstance(item, dict)
    }

    for signature in plan.functions:
        expected = selector_for_signature(signature)
        name = signature.split("(", 1)[0]
        actual = bridge_selectors.get(signature)
        ok = name in sol_source and name in rust_source and actual == expected
        selector_checks.append(
            {
                "signature": signature,
                "expected_selector": expected,
                "actual_selector": actual,
                "ok": ok,
            }
        )
        if not ok:
            errors.append(f"Function {signature} does not match across Solidity, Rust, and ABI selectors.")

    if plan.spec is not None:
        spec_signatures = [function.signature for function in plan.spec.functions]
        if spec_signatures != plan.functions:
            errors.append("Plan functions diverge from ApplicationSpec functions.")
        if artifacts.abi_bridge.get("application_type") != plan.spec.application_type:
            errors.append("ABI bridge application type diverges from ApplicationSpec.")

    if plan.direction != "EVM_TO_WASM":
        warnings.append("Only EVM_TO_WASM is exercised by the mock runtime.")

    return ValidationReport(
        status="SUCCESS" if not errors else "FAILURE",
        selector_checks=selector_checks,
        errors=errors,
        warnings=warnings,
    )
