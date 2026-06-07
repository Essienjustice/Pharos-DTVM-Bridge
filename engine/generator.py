from __future__ import annotations

from .schema import ApplicationSpec, FunctionSpec, GeneratedArtifacts, PlanOutput
from .template_registry import TemplateRegistry, render_template


def _solidity_params(function: FunctionSpec) -> str:
    return ", ".join(f"{param.type} {param.name}" for param in function.params)


def _solidity_returns(function: FunctionSpec) -> str:
    return f" returns ({function.returns})" if function.returns else ""


def _solidity_interface(spec: ApplicationSpec) -> str:
    lines = [f"interface {spec.interface_name} {{"]
    for function in spec.functions:
        mutability = " view" if function.mutability == "view" else ""
        lines.append(
            f"    function {function.name}({_solidity_params(function)}) external{mutability}{_solidity_returns(function)};"
        )
    lines.append("}")
    return "\n".join(lines)


def _solidity_wrappers(spec: ApplicationSpec) -> str:
    lines: list[str] = []
    for function in spec.functions:
        if function.mutability == "view":
            continue
        params = _solidity_params(function)
        args = ", ".join(param.name for param in function.params)
        returns = _solidity_returns(function)
        return_prefix = "return " if function.returns else ""
        wrapper_name = f"{function.name}ViaWasm"
        lines.extend(
            [
                f"    function {wrapper_name}({params}) external{returns} {{",
                f"        try target.{function.name}({args}) returns ({function.returns or 'uint256'} result) {{",
                f"            {return_prefix}result;",
                "        } catch {",
                "            revert(\"Cross-VM WASM call failed\");",
                "        }",
                "    }",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _rust_param_type(solidity_type: str) -> str:
    return {
        "address": "Address",
        "uint256": "U256",
        "bytes32": "B256",
        "bool": "bool",
    }.get(solidity_type, "U256")


def _rust_return_type(solidity_type: str | None) -> str:
    if solidity_type is None:
        return "()"
    return _rust_param_type(solidity_type)


def _rust_methods(spec: ApplicationSpec) -> str:
    lines: list[str] = []
    for index, function in enumerate(spec.functions):
        params = ", ".join(f"{param.name}: {_rust_param_type(param.type)}" for param in function.params)
        signature = f"    pub fn {function.name}(&mut self"
        if params:
            signature += f", {params}"
        signature += f") -> {_rust_return_type(function.returns)} {{"
        lines.append(signature)
        if function.returns == "bool":
            lines.append("        true")
        elif function.returns == "address":
            lines.append("        Address::ZERO")
        elif function.returns is None:
            lines.append("        ()")
        else:
            amount_param = next((param.name for param in function.params if param.type == "uint256"), None)
            if amount_param:
                lines.append(f"        {amount_param}")
            else:
                lines.append(f"        U256::from({index + 1})")
        lines.append("    }")
        lines.append("")
    return "\n".join(lines).rstrip()


def _storage_fields(spec: ApplicationSpec) -> str:
    lines: list[str] = []
    for index, item in enumerate(spec.contracts["wasm"].storage):
        name = item.split(":", 1)[0].strip()
        field_type = "uint256" if "uint256" in item else "bytes32"
        lines.append(f"        {field_type} {name}_{index};")
    return "\n".join(lines)


def _abi_json(spec: ApplicationSpec) -> str:
    import json

    entries = []
    for function in spec.functions:
        entries.append(
            {
                "type": "function",
                "name": function.name,
                "stateMutability": function.mutability,
                "inputs": [{"name": param.name, "type": param.type} for param in function.params],
                "outputs": [{"name": "", "type": function.returns}] if function.returns else [],
            }
        )
    for event in spec.contracts["wasm"].events:
        name = event.split("(", 1)[0]
        entries.append({"type": "event", "name": name, "signature": event})
    return json.dumps(entries, indent=2)


def generate_artifacts(plan: PlanOutput) -> GeneratedArtifacts:
    if plan.spec is None:
        raise ValueError("PlanOutput.spec is required for specification-driven generation.")

    spec = plan.spec
    templates = TemplateRegistry().load(spec.application_type)
    functions = [function.signature for function in spec.functions]
    selectors = [{"signature": signature, "selector": selector_for_signature(signature)} for signature in functions]
    values = {
        "wasm_contract": spec.contracts["wasm"].name,
        "evm_contract": spec.contracts["evm"].name,
        "interface_name": spec.interface_name,
        "solidity_interface": _solidity_interface(spec),
        "solidity_wrappers": _solidity_wrappers(spec),
        "rust_methods": _rust_methods(spec),
        "storage_fields": _storage_fields(spec),
        "abi_json": _abi_json(spec),
        "application_type": spec.application_type,
        "description": spec.description,
    }

    rust_source = render_template(templates["rust_contract"], values)
    solidity_source = render_template(templates["solidity_contract"], values)
    return GeneratedArtifacts(
        wasm_contract={
            "filename": f"generated/{spec.application_type}/src/lib.rs",
            "language": "rust",
            "framework": "stylus-sdk",
            "contract_name": spec.contracts["wasm"].name,
            "storage_model": spec.contracts["wasm"].storage,
            "events": spec.contracts["wasm"].events,
            "source": rust_source,
        },
        evm_contract={
            "filename": f"generated/{spec.application_type}/Caller.sol",
            "language": "solidity",
            "solc_version": "^0.8.20",
            "contract_name": spec.contracts["evm"].name,
            "storage_model": spec.contracts["evm"].storage,
            "events": spec.contracts["evm"].events,
            "source": solidity_source,
        },
        abi_bridge={
            "interface": spec.interface_name,
            "direction": spec.direction,
            "application_type": spec.application_type,
            "functions": functions,
            "selectors": selectors,
            "abi": render_template(templates["abi"], values),
        },
        rust_source=f"{spec.contracts['wasm'].name} {spec.application_type} source rendered",
        solidity_source=f"{spec.contracts['evm'].name} {spec.application_type} source rendered",
    )


def selector_for_signature(signature: str) -> str:
    from web3 import Web3

    return "0x" + Web3.keccak(text=signature).hex()[:8]


class Generator:
    def generate(self, plan: PlanOutput) -> GeneratedArtifacts:
        return generate_artifacts(plan)
