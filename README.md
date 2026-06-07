# pharos-dtvm-bridge

**Cross-VM AI Contract Agent for Pharos DTVM**

`pharos-dtvm-bridge` turns a natural-language cross-VM contract request into Solidity + Rust/WASM artifacts, validates ABI compatibility, simulates deployment order, and traces EVM -> WASM execution in a deterministic Pharos DTVM mock runtime.

## Quick Start

Run the screenshot-ready demo:

```bash
python demo/run_demo.py
```

Run the branded CLI:

```bash
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity"
```

Run a deterministic failure simulation:

```bash
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity" --simulate abi_mismatch
```

## Why This Matters

Pharos DTVM enables EVM bytecode and WASM bytecode to execute in one deterministic environment. That means a Solidity contract can call a Rust/WASM contract as part of the same transaction flow.

The hard part is not the idea. The hard part is the boundary:

- Solidity and Rust must agree on selectors, types, argument order, and return encoding.
- WASM contracts must be deployed before EVM callers can safely target them.
- Reverts can happen in Solidity, at the cross-VM ABI boundary, or inside the WASM callee.

This project automates that loop with an AI-style contract agent. It plans the cross-VM interaction, generates both sides, validates the ABI bridge, simulates deployment, and produces a trace-like result that explains success or failure.

## How It Works

Pipeline:

```text
User Prompt
  -> Planner
  -> Generator
  -> Validator
  -> Deployer
  -> Tracer
  -> Logs + JSON Output
```

Each run produces two synchronized outputs:

- human-readable logs for terminal review
- structured JSON for tooling, judging, or downstream automation

Example log stages:

```text
[PLAN] Cross-VM intent detected: EVM_TO_WASM
[GENERATOR] Solidity + Rust contracts generated
[VALIDATOR] ABI compatibility OK
[DEPLOYER] WASM deployed -> 0x...
[DEPLOYER] EVM deployed -> 0x...
[TRACER] Cross-VM execution SUCCESS
```

## Example Execution

Input:

```bash
python cli.py "Write a Solidity contract that calls a Rust mint function"
```

Success output begins with:

```text
[PLAN] Planner started
[PLAN] Cross-VM intent detected: EVM_TO_WASM
[GENERATOR] Generator started
[GENERATOR] Solidity + Rust contracts generated (SolidityMintCaller -> RustWasmMinter)
[VALIDATOR] Validator started
[VALIDATOR] ABI compatibility OK
[DEPLOYER] Deploy order: WASM_FIRST
[DEPLOYER] WASM deployed -> 0x0000000000000000000000000000000000000001
[DEPLOYER] EVM deployed -> 0x0000000000000000000000000000000000000002
[TRACER] Tracer started
[TRACER] Cross-VM execution SUCCESS
```

The final JSON includes:

```json
{
  "skill": "pharos-dtvm-bridge",
  "status": "SUCCESS",
  "runtime": "mock",
  "simulation_mode": "success",
  "plan": {
    "direction": "EVM_TO_WASM",
    "functions": ["mint(uint256)"]
  },
  "trace": {
    "cross_vm_boundary_detected": true,
    "failure_class": null
  }
}
```

Failure example:

```bash
python cli.py "Write a Solidity contract that calls a Rust mint function" --simulate abi_mismatch
```

The logs identify the failure:

```text
[TRACER] Cross-VM execution FAILED: ABI_MISMATCH - EVM calldata selector did not match any exported WASM function selector.
```

The JSON carries the same state in `trace.failure_class`, `trace.failure_detail`, and `errors`.

## Failure Simulation Capability

The mock runtime is deterministic and supports judge-friendly failure modes:

| Mode | What It Demonstrates |
| --- | --- |
| `success` | Normal EVM -> WASM call, return value, and trace |
| `abi_mismatch` | Solidity calldata selector does not match the WASM export |
| `wasm_revert` | Dispatch reaches WASM, then the WASM contract reverts |
| `deploy_order_error` | EVM caller is attempted before a valid WASM target is available |

Run any mode with:

```bash
python cli.py "Write a Solidity contract that calls a Rust mint function" --simulate wasm_revert
```

## Real-World Usage & Developer Value

This repository models how developers can use an agent in real Pharos cross-VM workflows.

It helps as:

- a **contract generator** for Solidity callers and Rust/WASM targets
- a **pre-deployment validator** for ABI selector and deployment-order assumptions
- a **debugging tool** for failed WASM <-> EVM calls
- an **educational system** for understanding DTVM execution flow

Concrete scenarios:

- **Writing cross-VM DeFi contracts**: generate a Solidity-facing DeFi entry point that delegates compute-heavy logic to Rust/WASM.
- **Debugging failed WASM <-> EVM calls**: simulate `abi_mismatch` or `wasm_revert` and inspect the trace-compatible call tree.
- **Validating ABI correctness before deployment**: confirm selectors such as `mint(uint256)` resolve consistently before using a real Pharos RPC.

## How To Run

Run the CLI:

```bash
python cli.py "Write a Solidity contract that calls a Rust mint function"
```

Run a simulated failure:

```bash
python cli.py "Write a Solidity contract that calls a Rust mint function" --simulate abi_mismatch
```

Run the branded wrapper:

```bash
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity"
```

Run the demo:

```bash
python demo/run_demo.py
```

The demo prints a success case and an ABI mismatch failure case, each with readable logs followed by structured JSON.

## Repository Layout

```text
cli.py                     Main CLI entry point
bin/pharos-dtvm-bridge.py  Branded CLI wrapper
engine/                    Planner, generator, validator, deployer, tracer
demo/run_demo.py           Screenshot-ready success/failure demo
contracts/                 Solidity + Rust/WASM scaffolds
scripts/                   Selector, deploy, and trace helpers
docs/                      Supporting interface and deployment notes
```

## Notes

The primary demo path uses the deterministic mock runtime. Real deployment helpers are included for Pharos development workflows, but the submission demo does not require RPC access, private keys, Foundry, or cargo-stylus.
