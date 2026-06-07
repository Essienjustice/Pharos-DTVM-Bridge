# Changelog

## v1.0.0 - Competition Submission

### Added

- End-to-end deterministic pipeline for Pharos DTVM cross-VM contract generation and simulation.
- Planner stage for interpreting natural-language cross-VM intents.
- Specification builder for ERC20, NFT, voting, escrow, oracle, and staking application specs.
- Template-backed generator stage for materially different Solidity caller and Rust/WASM target artifacts.
- Mock compiler stage for deterministic generated-source validation.
- Validator stage for ABI selector compatibility checks.
- Deployer stage with WASM-first mock deployment ordering.
- Tracer stage with trace-compatible cross-VM call output.
- Deterministic mock runtime with stable addresses and transaction hashes.
- Failure simulation modes:
  - `abi_mismatch`
  - `wasm_revert`
  - `deploy_order_error`
- CLI entry point with structured JSON and human-readable logs.
- Branded CLI wrapper at `bin/pharos-dtvm-bridge.py`.
- Demo runner showing one success case and one ABI mismatch failure case.
- Submission polish: README, release notes, reproducibility guide, architecture documentation, and release checklist.

### Notes

- The submission demo uses mock runtime only.
- Real deployment helper scripts are included but are outside the deterministic competition path.
