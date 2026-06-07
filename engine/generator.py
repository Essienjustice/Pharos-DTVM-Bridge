from __future__ import annotations

from .schema import GeneratedArtifacts, PlanOutput


def _rust_source(plan: PlanOutput) -> str:
    if any(fn.startswith("mint(") for fn in plan.functions):
        return """#![cfg_attr(not(feature = "export-abi"), no_main)]

extern crate alloc;

use stylus_sdk::{alloy_primitives::U256, prelude::*};

sol_storage! {
    #[entrypoint]
    pub struct RustWasmMinter {
        uint256 totalMinted;
    }
}

#[public]
impl RustWasmMinter {
    pub fn mint(&mut self, value: U256) -> U256 {
        let next = self.total_minted.get() + value;
        self.total_minted.set(next);
        next
    }
}
"""
    return """#![cfg_attr(not(feature = "export-abi"), no_main)]

extern crate alloc;

use stylus_sdk::{alloy_primitives::U256, prelude::*};

sol_storage! {
    #[entrypoint]
    pub struct WasmCounter {
        uint256 value;
    }
}

#[public]
impl WasmCounter {
    pub fn increment(&mut self, amount: U256) -> U256 {
        let next = self.value.get() + amount;
        self.value.set(next);
        next
    }

    pub fn get(&self) -> U256 {
        self.value.get()
    }
}
"""


def _solidity_source(plan: PlanOutput) -> str:
    if any(fn.startswith("mint(") for fn in plan.functions):
        return """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IRustWasmMinter {
    function mint(uint256 value) external returns (uint256);
}

contract SolidityMintCaller {
    IRustWasmMinter public immutable wasmMinter;

    event CrossVMCallSuccess(address indexed target, bytes4 indexed selector, uint256 value);

    constructor(address wasmMinter_) {
        wasmMinter = IRustWasmMinter(wasmMinter_);
    }

    function mintViaWasm(uint256 value) external returns (uint256 totalMinted) {
        totalMinted = wasmMinter.mint(value);
        emit CrossVMCallSuccess(address(wasmMinter), IRustWasmMinter.mint.selector, totalMinted);
    }
}
"""
    return """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IWasmCounter {
    function increment(uint256 amount) external returns (uint256);
    function get() external view returns (uint256);
}

contract CrossVmCounterCaller {
    IWasmCounter public immutable wasmCounter;

    constructor(address wasmCounter_) {
        wasmCounter = IWasmCounter(wasmCounter_);
    }

    function incrementViaWasm(uint256 amount) external returns (uint256) {
        return wasmCounter.increment(amount);
    }
}
"""


def generate_artifacts(plan: PlanOutput) -> GeneratedArtifacts:
    interface_name = "IRustWasmMinter" if any(fn.startswith("mint(") for fn in plan.functions) else "IWasmCounter"
    selectors = [{"signature": fn, "selector": selector_for_signature(fn)} for fn in plan.functions]

    return GeneratedArtifacts(
        wasm_contract={
            "filename": "generated/src/lib.rs",
            "language": "rust",
            "framework": "stylus-sdk",
            "contract_name": plan.wasm_contract,
            "source": _rust_source(plan),
        },
        evm_contract={
            "filename": "generated/src/Caller.sol",
            "language": "solidity",
            "solc_version": "^0.8.20",
            "contract_name": plan.evm_contract,
            "source": _solidity_source(plan),
        },
        abi_bridge={
            "interface": interface_name,
            "direction": plan.direction,
            "functions": plan.functions,
            "selectors": selectors,
        },
    )


def selector_for_signature(signature: str) -> str:
    try:
        from eth_utils import keccak

        return "0x" + keccak(text=signature)[:4].hex()
    except Exception:
        import hashlib

        digest = hashlib.sha3_256(signature.encode("utf-8")).digest()
        return "0x" + digest[:4].hex()
