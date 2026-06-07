from __future__ import annotations

from .mock_runtime import MockRuntime
from .schema import DeploymentResult, PlanOutput, TraceResult, ValidationReport


def trace_cross_vm_call(
    plan: PlanOutput,
    validation: ValidationReport,
    deployment: DeploymentResult,
    runtime: MockRuntime,
) -> TraceResult:
    if validation.status != "SUCCESS" or deployment.status != "SUCCESS":
        failure = deployment.failure or {
            "error_type": "PRECONDITION_FAILED",
            "failed_stage": "tracer",
            "explanation": "Validation or deployment failed before trace simulation.",
        }
        return TraceResult(
            status="FAILURE",
            tx_hash=deployment.deploy_tx_evm or deployment.deploy_tx_wasm,
            call_tree={
                "type": "CALL",
                "from": "",
                "to": deployment.evm_address or deployment.wasm_address,
                "input": plan.functions[0] if plan.functions else "",
                "output": "0x",
                "error": failure["error_type"],
                "calls": [],
            },
            cross_vm_boundary_detected=False,
            failure_class=str(failure["error_type"]),
            failure_detail=str(failure["explanation"]),
            failure=failure,
        )

    function = plan.functions[0]
    call = runtime.call_cross_vm(deployment.evm_address, function)
    call_tree = call["call_tree"]
    failure = call.get("failure")

    if isinstance(failure, dict):
        return TraceResult(
            status="FAILURE",
            tx_hash=str(call["tx_hash"]),
            call_tree=call_tree,
            cross_vm_boundary_detected=bool(call_tree.get("calls")),
            failure_class=str(failure["error_type"]),
            failure_detail=str(failure["explanation"]),
            failure=failure,
        )

    return TraceResult(
        status="SUCCESS",
        tx_hash=str(call["tx_hash"]),
        call_tree=call_tree,
        cross_vm_boundary_detected=bool(call_tree.get("calls")),
        failure_class=None,
        failure_detail=None,
    )
