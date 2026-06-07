# Agent Interface

All operational scripts emit the same JSON envelope:

```json
{
  "skill": "pharos-dtvm-bridge",
  "version": "1.0.0",
  "action": "GENERATE | VALIDATE | DEPLOY | TRACE | DEBUG | SETUP",
  "network": "mainnet | testnet",
  "chain_id": 1672,
  "status": "SUCCESS | FAILURE | PARTIAL",
  "artifacts": {},
  "trace": {},
  "errors": [],
  "next_steps": []
}
```

## ABI Bridge

The Solidity interface in `contracts/evm/interfaces/IWasmCounter.sol` and the Rust `sol!` block in `contracts/wasm-counter/src/lib.rs` are the source of truth for the cross-VM boundary.

Current function selectors:

| Function | Selector |
| --- | --- |
| `increment(uint256)` | `0x7cf5dab0` |
| `get()` | `0x6d4ce63c` |
| `setOwner(address)` | `0x13af4035` |

Run `python scripts/check_selectors.py` after changing either side.

## Failure Classification

`scripts/trace_tx.py` maps `debug_traceTransaction` call traces into:

| Class | Meaning |
| --- | --- |
| `ABI_MISMATCH` | Nested call had no usable output, often a selector or type mismatch |
| `NO_CODE` | Caller points at an address without deployed contract code |
| `WASM_REVERT` | Nested frame reverted inside the WASM target |
| `GAS` | Trace includes a gas-related failure |
| `DEPLOY_ORDER` | EVM caller was deployed or configured before a valid WASM address existed |
| `SILENT` | Transaction failed or had no state change without a clear revert reason |
| `EVM_REVERT` | Solidity caller reverted before visible cross-VM dispatch |
