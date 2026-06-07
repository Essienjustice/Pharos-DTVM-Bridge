from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentRequest:
    intent: str
    network: str = "testnet"
    use_mock_runtime: bool = True
    simulation_mode: str = "success"

    @classmethod
    def from_intent(
        cls,
        intent: str,
        network: str = "testnet",
        simulation_mode: str = "success",
    ) -> "AgentRequest":
        return cls(
            intent=intent.strip(),
            network=network,
            use_mock_runtime=True,
            simulation_mode=simulation_mode,
        )


@dataclass(frozen=True)
class FunctionParam:
    name: str
    type: str


@dataclass(frozen=True)
class FunctionSpec:
    name: str
    params: list[FunctionParam]
    returns: str | None = None
    mutability: str = "nonpayable"

    @property
    def signature(self) -> str:
        return f"{self.name}({','.join(param.type for param in self.params)})"


@dataclass(frozen=True)
class ContractSpec:
    name: str
    storage: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ApplicationSpec:
    application_type: str
    direction: str
    contracts: dict[str, ContractSpec]
    functions: list[FunctionSpec]
    interface_name: str
    description: str


@dataclass(frozen=True)
class PlanOutput:
    action: str
    direction: str
    wasm_contract: str
    evm_contract: str
    functions: list[str]
    network: str
    application_type: str = "generic"
    spec: ApplicationSpec | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GeneratedArtifacts:
    wasm_contract: dict[str, Any]
    evm_contract: dict[str, Any]
    abi_bridge: dict[str, Any]
    rust_source: str = ""
    solidity_source: str = ""


@dataclass(frozen=True)
class ValidationReport:
    status: str
    selector_checks: list[dict[str, Any]]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompilationResult:
    success: bool
    mode: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentResult:
    status: str
    network: str
    chain_id: int
    wasm_address: str
    evm_address: str
    deploy_tx_wasm: str
    deploy_tx_evm: str
    deploy_order: str = "WASM_FIRST"
    errors: list[str] = field(default_factory=list)
    failure: dict[str, Any] | None = None


@dataclass(frozen=True)
class TraceResult:
    status: str
    tx_hash: str
    call_tree: dict[str, Any]
    cross_vm_boundary_detected: bool
    failure_class: str | None = None
    failure_detail: str | None = None
    detail: str | None = None
    failure: dict[str, Any] | None = None


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
