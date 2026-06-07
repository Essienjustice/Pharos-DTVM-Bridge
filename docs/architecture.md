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
  | Planner   | ----> | Spec      | ----> | Generator   |
  +-----------+       | Builder   |       +------+------+
                      +-----------+              |
                                                 v
                                          +-------------+
                                          | Validator   |
                                          +------+------+
                                                |
                                                v
                                        +---------------+
                                        | Compiler      |
                                        | Mock syntax   |
                                        +-------+-------+
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

`engine/planner.py` coordinates planning around the structured application specification and chooses:

- action
- direction
- contract names
- function signatures
- network metadata

### Spec Builder

`engine/spec_builder.py` converts a natural-language prompt into an `ApplicationSpec`.

`engine/archetypes.py` classifies prompts into supported archetypes:

- ERC20
- NFT
- Voting
- Escrow
- Oracle
- Staking

The application spec is the source of truth for generated contract names, storage models, events, functions, and ABI definitions.

### Generator

`engine/generator.py` renders templates from `templates/` into in-memory Solidity and Rust/WASM artifact representations and selector metadata.

### Validator

`engine/validator.py` checks that the generated Solidity and Rust artifacts share the expected function names and selectors.

### Compiler

`engine/compiler.py` provides a mock compilation layer for deterministic syntax checks. It also contains a real-mode command runner for `forge build`, `cargo check`, and `cargo stylus check` when external tools are available.

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

`engine/runtime/base.py` defines the runtime protocol, `engine/runtime/mock_runtime.py` re-exports the deterministic mock runtime, and `engine/runtime/real_runtime.py` provides extensible command placeholders for live Pharos tooling.

## Data Flow

The pipeline uses dataclasses from `engine/schema.py`:

```text
AgentRequest
  -> PlanOutput
  -> ApplicationSpec
  -> GeneratedArtifacts
  -> ValidationReport
  -> CompilationResult
  -> DeploymentResult
  -> TraceResult
```

The final pipeline result is a JSON-serializable dictionary containing each stage output plus synchronized execution logs.
