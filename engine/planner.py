from __future__ import annotations

from .schema import AgentRequest, PlanOutput
from .spec_builder import build_application_spec


def create_plan(request: AgentRequest) -> PlanOutput:
    intent = request.intent.lower()
    spec = build_application_spec(request.intent)
    action = "GENERATE"
    direction = spec.direction
    functions = [function.signature for function in spec.functions]
    wasm_contract = spec.contracts["wasm"].name
    evm_contract = spec.contracts["evm"].name
    notes = [
        "Mock runtime selected; no network deployment will be attempted.",
        f"Application archetype classified as {spec.application_type}.",
    ]

    if "rust" in intent and "solidity" in intent:
        notes.append("Intent requests Rust and Solidity cross-VM artifacts.")
    if "solidity" in intent and "calls" in intent:
        direction = "EVM_TO_WASM"

    return PlanOutput(
        action=action,
        direction=direction,
        wasm_contract=wasm_contract,
        evm_contract=evm_contract,
        functions=functions,
        network=request.network,
        application_type=spec.application_type,
        spec=spec,
        notes=notes,
    )


class Planner:
    def plan(self, intent: str) -> PlanOutput:
        return create_plan(AgentRequest.from_intent(intent))
