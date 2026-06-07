# Reproducibility

This guide is for reviewers starting from a fresh clone.

## 1. Fresh Clone

```bash
git clone <repository-url>
cd pharos-dtvm-bridge
```

If the directory name differs, run commands from the repository root.

## 2. Python Setup

Python 3.10+ is recommended.

```bash
python --version
```

Optional virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

The demo path uses the deterministic mock runtime and does not require RPC access, Foundry, cargo-stylus, or private keys.

## 4. Run Demo

```bash
python demo/run_demo.py
```

Expected behavior:

- prints `=== SUCCESS CASE ===`
- prints pipeline logs
- prints structured JSON with `"status": "SUCCESS"`
- prints `=== FAILURE CASE: ABI MISMATCH ===`
- prints structured JSON with `"status": "FAILURE"` and `"failure_class": "ABI_MISMATCH"`

## 5. Run CLI

```bash
python cli.py "Write a Solidity contract that calls a Rust mint function"
```

Expected behavior:

- logs planner, generator, validator, deployer, and tracer stages
- final JSON has `"runtime": "mock"`
- final JSON has `"status": "SUCCESS"`

Run the branded wrapper:

```bash
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity"
```

Run a deterministic failure:

```bash
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity" --simulate wasm_revert
```

Expected failure output:

- process exits cleanly
- final JSON has `"status": "FAILURE"`
- final JSON includes `trace.failure_class`

## 6. Compile Check

```bash
python -m compileall cli.py engine demo bin
```

Expected behavior: command completes without syntax errors.

## Troubleshooting

### `ModuleNotFoundError`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### PowerShell quoting issues

Use double quotes around the prompt:

```bash
python cli.py "Write a Solidity contract that calls a Rust mint function"
```

### Real deployment tools missing

The competition demo does not require real deployment tools. Foundry, cargo-stylus, and Pharos RPC settings are only needed for the optional real deployment helper scripts.

### Python package warning about `pkg_resources`

`requirements.txt` pins `setuptools<82` so Web3 can import consistently in current Python environments.
