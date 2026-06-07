from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Archetype:
    key: str
    label: str
    keywords: tuple[str, ...]


ARCHETYPES: dict[str, Archetype] = {
    "erc20": Archetype("erc20", "ERC20", ("erc20", "token", "coin", "fungible", "transfer")),
    "nft": Archetype("nft", "NFT", ("nft", "erc721", "collectible", "metadata", "non-fungible")),
    "voting": Archetype("voting", "Voting", ("vote", "voting", "proposal", "governance", "dao")),
    "escrow": Archetype("escrow", "Escrow", ("escrow", "deposit", "release", "arbiter", "buyer", "seller")),
    "oracle": Archetype("oracle", "Oracle", ("oracle", "price", "feed", "data", "quote")),
    "staking": Archetype("staking", "Staking", ("stake", "staking", "reward", "unstake", "yield")),
}


def classify_archetype(prompt: str) -> Archetype:
    normalized = prompt.lower()
    for archetype in ARCHETYPES.values():
        if any(keyword in normalized for keyword in archetype.keywords):
            return archetype
    return ARCHETYPES["erc20"]
