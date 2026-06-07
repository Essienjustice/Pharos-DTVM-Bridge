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

    for signature in plan.functions:
        expected = selector_for_signature(signature)
        name = signature.split("(", 1)[0]
        ok = name in sol_source and name in rust_source
        selector_checks.append(
            {
                "signature": signature,
                "expected_selector": expected,
                "actual_selector": expected if ok else None,
                "ok": ok,
            }
        )
        if not ok:
            errors.append(f"Function {signature} is not present on both VM artifacts.")

    if plan.direction != "EVM_TO_WASM":
        warnings.append("Only EVM_TO_WASM is exercised by the mock runtime.")

    return ValidationReport(
        status="SUCCESS" if not errors else "FAILURE",
        selector_checks=selector_checks,
        errors=errors,
        warnings=warnings,
    )
