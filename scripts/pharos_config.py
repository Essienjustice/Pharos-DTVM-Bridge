from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Network:
    name: str
    chain_id: int
    rpc: str
    explorer: str
    native: str
    wss: str | None = None


NETWORKS: dict[str, Network] = {
    "testnet": Network(
        name="testnet",
        chain_id=688689,
        rpc=os.getenv("PHAROS_TESTNET_RPC", "https://atlantic.dplabs-internal.com"),
        wss=os.getenv("PHAROS_TESTNET_WSS", "wss://atlantic.dplabs-internal.com"),
        explorer="https://atlantic.pharosscan.xyz",
        native="PHRS",
    ),
    "mainnet": Network(
        name="mainnet",
        chain_id=1672,
        rpc=os.getenv("PHAROS_MAINNET_RPC", "https://rpc.pharos.xyz"),
        wss=None,
        explorer="https://www.pharosscan.xyz",
        native="PROS",
    ),
}


def get_network(name: str | None) -> Network:
    selected = name or os.getenv("PHAROS_NETWORK", "testnet")
    if selected not in NETWORKS:
        known = ", ".join(sorted(NETWORKS))
        raise ValueError(f"Unknown network '{selected}'. Expected one of: {known}")
    return NETWORKS[selected]


def envelope(action: str, network: Network, status: str, **extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "skill": "pharos-dtvm-bridge",
        "version": "1.0.0",
        "action": action,
        "network": network.name,
        "chain_id": network.chain_id,
        "status": status,
        "artifacts": {},
        "trace": {},
        "errors": [],
        "next_steps": [],
    }
    base.update(extra)
    return base
