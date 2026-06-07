# Architecture

This document reflects the current implementation only.

## Pipeline Diagram

```text
                    +----------------+
User prompt ------> | cli.py / bin   |
                    +-------+--------+
                            |
                            v
                    +----------------+
                    | run_pipeline   |
                    +-------+--------+
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
  +-----------+       +-----------+       +-------------+
  | Planner   | ----> | Generator | ----> | Validator   |
  +-----------+       +-----------+       +-------------+
                                                |
                                                v
                                        +---------------+
                                        | Deployer      |
                                        | MockRuntime   |
                                        +-------+-------+
                                                |
                                                v
                                        +---------------+
                                        | Tracer        |
                                        | MockRuntime   |
                                        +-------+-------+
                                                |
                                                v
                                  Human logs + JSON result
```

## Stage Responsibilities

### CLI

`cli.py` parses user input and simulation flags, creates an `AgentRequest`, calls `run_pipeline`, then prints logs and JSON.

`bin/pharos-dtvm-bridge.py` is a branded wrapper around `cli.py`.

### Planner

`engine/planner.py` interprets the intent and chooses:

- action
- direction
- contract names
- function signatures
- network metadata

### Generator

`engine/generator.py` creates in-memory Solidity and Rust/WASM artifact representations and selector metadata.

### Validator

`engine/validator.py` checks that the generated Solidity and Rust artifacts share the expected function names and selectors.

### Deployer

`engine/deployer.py` uses `MockRuntime` to simulate WASM-first deployment and EVM caller deployment.

### Tracer

`engine/tracer.py` simulates a cross-VM call and produces trace-compatible output, including failure classification when requested.

### Mock Runtime

`engine/mock_runtime.py` provides deterministic addresses, transaction hashes, call trees, and failure modes:

- `success`
- `abi_mismatch`
- `wasm_revert`
- `deploy_order_error`

It is the only runtime used by the submission demo.

## Data Flow

The pipeline uses dataclasses from `engine/schema.py`:

```text
AgentRequest
  -> PlanOutput
  -> GeneratedArtifacts
  -> ValidationReport
  -> DeploymentResult
  -> TraceResult
```

The final pipeline result is a JSON-serializable dictionary containing each stage output plus synchronized execution logs.
