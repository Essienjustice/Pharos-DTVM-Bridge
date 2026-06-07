from __future__ import annotations

from .schema import AgentRequest, PlanOutput


def create_plan(request: AgentRequest) -> PlanOutput:
    intent = request.intent.lower()
    action = "GENERATE"
    direction = "EVM_TO_WASM"

    functions = ["mint(uint256)"]
    wasm_contract = "RustWasmMinter"
    evm_contract = "SolidityMintCaller"
    notes = ["Mock runtime selected; no network deployment will be attempted."]

    if "transfer" in intent:
        functions = ["transfer(address,uint256)"]
    elif "counter" in intent or "increment" in intent:
        functions = ["increment(uint256)", "get()"]
        wasm_contract = "WasmCounter"
        evm_contract = "CrossVmCounterCaller"

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
        notes=notes,
    )
