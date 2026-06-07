from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "templates"


class TemplateRegistry:
    def __init__(self, template_root: Path = TEMPLATE_ROOT) -> None:
        self.template_root = template_root

    def load(self, application_type: str) -> dict[str, Any]:
        directory = self.template_root / application_type
        if not directory.exists():
            raise ValueError(f"No template directory found for application type: {application_type}")

        spec_path = directory / "spec.json"
        return {
            "spec": json.loads(spec_path.read_text(encoding="utf-8")),
            "rust_contract": (directory / "rust_contract.template").read_text(encoding="utf-8"),
            "solidity_contract": (directory / "solidity_contract.template").read_text(encoding="utf-8"),
            "abi": (directory / "abi.template").read_text(encoding="utf-8"),
        }


def render_template(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered
