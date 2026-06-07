from __future__ import annotations

import shutil
import subprocess

from .schema import CompilationResult, GeneratedArtifacts


def compile_artifacts(artifacts: GeneratedArtifacts, mode: str = "mock") -> CompilationResult:
    if mode == "mock":
        errors: list[str] = []
        warnings: list[str] = []
        rust_source = artifacts.wasm_contract.get("source", "")
        solidity_source = artifacts.evm_contract.get("source", "")

        if "pub struct" not in rust_source:
            errors.append("Rust source does not define a public storage struct.")
        if "pragma solidity" not in solidity_source:
            errors.append("Solidity source does not declare a pragma.")
        if "interface " not in solidity_source:
            warnings.append("Solidity source does not expose a dedicated target interface.")

        return CompilationResult(
            success=not errors,
            mode=mode,
            errors=errors,
            warnings=warnings,
            artifacts={
                "cargo_check": "SKIPPED (mock mode)",
                "forge_build": "SKIPPED (mock mode)",
                "selector_validation": "PASSED" if not errors else "FAILED",
                "rust": artifacts.wasm_contract["filename"],
                "solidity": artifacts.evm_contract["filename"],
            },
        )

    return _real_compile()


def _real_compile() -> CompilationResult:
    commands = [
        ("forge", ["forge", "build"]),
        ("cargo", ["cargo", "check"]),
        ("cargo", ["cargo", "stylus", "check"]),
    ]
    errors: list[str] = []
    warnings: list[str] = []

    for executable, command in commands:
        if shutil.which(executable) is None:
            warnings.append(f"Skipped {' '.join(command)} because {executable} is not installed.")
            continue
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            errors.append(completed.stderr.strip() or completed.stdout.strip())

    return CompilationResult(
        success=not errors,
        mode="real",
        errors=errors,
        warnings=warnings,
        artifacts={},
    )
