# v1.0.0 - Competition Submission Release

## Project Summary

`pharos-dtvm-bridge` is a Cross-VM AI Contract Agent for Pharos DTVM. It converts a natural-language request into specification-driven Solidity + Rust/WASM artifacts, validates ABI compatibility, simulates WASM-first deployment, and produces trace-compatible output.

## Why It Matters for Pharos

Pharos DTVM enables Solidity/EVM and Rust/WASM contracts to interact in one execution environment. This project demonstrates how an agent can reduce integration risk around selectors, ABI encoding, deployment order, and cross-VM failure diagnosis.

## Major Features

- Natural-language CLI workflow
- Planner -> spec builder -> generator -> validator -> compiler -> deployer -> tracer pipeline
- ERC20, NFT, voting, escrow, oracle, and staking archetype generation
- Template-backed Solidity, Rust/WASM, and ABI outputs
- Deterministic mock runtime
- Human-readable logs plus structured JSON output
- Failure simulation for ABI mismatch, WASM revert, and deploy-order errors
- Solidity and Rust/WASM contract scaffolds
- Screenshot-ready demo runner

## Demo Instructions

```bash
python demo/run_demo.py
```

Run the branded CLI:

```bash
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity"
```

Run a simulated failure:

```bash
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity" --simulate abi_mismatch
```

## Known Limitations

- The submission path uses a deterministic mock runtime, not a live Pharos RPC.
- Generated contracts are scaffold artifacts, not audited production contracts.
- Real deployment helpers require external tooling such as Foundry, cargo-stylus, and funded keys.

## Future Roadmap

- Live Pharos RPC validation mode.
- Expanded ABI type coverage.
- Richer trace parsing for live `debug_traceTransaction` output.
- Additional contract templates for DeFi and account abstraction workflows.
