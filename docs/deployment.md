# Deployment

## Preflight

```bash
rustup target add wasm32-unknown-unknown
cargo stylus --help
forge --version
cast --version
python -m pip install -r requirements.txt
```

If Windows reports `can't find crate for core` while the WASM target is installed, check that `%USERPROFILE%\.cargo\bin` appears before standalone Rust install directories on `PATH`.

Set `.env`:

```bash
PHAROS_NETWORK=testnet
PRIVATE_KEY=0x...
```

## Deploy

```bash
python scripts/deploy.py --network testnet
```

The deployment script writes `deployments/testnet.json` or `deployments/mainnet.json`.

## Manual Commands

```bash
cd contracts/wasm-counter
cargo stylus check --endpoint=https://atlantic.dplabs-internal.com
cargo stylus deploy --private-key=$PRIVATE_KEY --endpoint=https://atlantic.dplabs-internal.com
```

Then deploy the Solidity caller:

```bash
forge create contracts/evm/CrossVmCounterCaller.sol:CrossVmCounterCaller \
  --constructor-args <WASM_ADDRESS> \
  --private-key $PRIVATE_KEY \
  --rpc-url https://atlantic.dplabs-internal.com
```

Dry-run:

```bash
cast call <EVM_CALLER> "readWasmCounter()(uint256)" --rpc-url https://atlantic.dplabs-internal.com
```
