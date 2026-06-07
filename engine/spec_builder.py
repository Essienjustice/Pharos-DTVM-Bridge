from __future__ import annotations

from .archetypes import classify_archetype
from .schema import ApplicationSpec, ContractSpec, FunctionParam, FunctionSpec


def _fn(
    name: str,
    params: list[tuple[str, str]],
    returns: str | None = "uint256",
    mutability: str = "nonpayable",
) -> FunctionSpec:
    return FunctionSpec(
        name=name,
        params=[FunctionParam(param_name, param_type) for param_name, param_type in params],
        returns=returns,
        mutability=mutability,
    )


def build_application_spec(prompt: str) -> ApplicationSpec:
    archetype = classify_archetype(prompt)
    key = archetype.key
    direction = "EVM_TO_WASM"

    definitions = {
        "erc20": {
            "wasm": ContractSpec(
                name="RustERC20",
                storage=["balances: mapping(address => uint256)", "totalSupply: uint256"],
                events=["Transfer(address indexed from,address indexed to,uint256 value)"],
            ),
            "evm": ContractSpec(
                name="SolidityERC20Caller",
                storage=["tokenTarget: address"],
                events=["CrossVMTransfer(address indexed target,address indexed to,uint256 amount)"],
            ),
            "interface": "IRustERC20",
            "functions": [
                _fn("mint", [("to", "address"), ("amount", "uint256")]),
                _fn("transfer", [("to", "address"), ("amount", "uint256")], "bool"),
                _fn("balanceOf", [("owner", "address")], "uint256", "view"),
            ],
            "description": "Fungible token contract implemented in Rust/WASM and called from Solidity.",
        },
        "nft": {
            "wasm": ContractSpec(
                name="RustNFT",
                storage=["owners: mapping(uint256 => address)", "tokenUri: mapping(uint256 => string)"],
                events=["Transfer(address indexed from,address indexed to,uint256 indexed tokenId)"],
            ),
            "evm": ContractSpec(
                name="SolidityNFTCaller",
                storage=["nftTarget: address"],
                events=["CrossVMMint(address indexed target,address indexed to,uint256 tokenId)"],
            ),
            "interface": "IRustNFT",
            "functions": [
                _fn("mintNft", [("to", "address"), ("tokenId", "uint256")]),
                _fn("ownerOf", [("tokenId", "uint256")], "address", "view"),
                _fn("setTokenUri", [("tokenId", "uint256"), ("uriHash", "bytes32")], "bool"),
            ],
            "description": "NFT ownership and metadata bridge with a Solidity caller.",
        },
        "voting": {
            "wasm": ContractSpec(
                name="RustVoting",
                storage=["votes: mapping(uint256 => uint256)", "hasVoted: mapping(address => bool)"],
                events=["VoteCast(address indexed voter,uint256 indexed proposalId,uint256 weight)"],
            ),
            "evm": ContractSpec(
                name="SolidityVotingCaller",
                storage=["votingTarget: address"],
                events=["CrossVMVote(address indexed target,uint256 indexed proposalId)"],
            ),
            "interface": "IRustVoting",
            "functions": [
                _fn("vote", [("proposalId", "uint256")]),
                _fn("proposalVotes", [("proposalId", "uint256")], "uint256", "view"),
                _fn("hasVoted", [("voter", "address")], "bool", "view"),
            ],
            "description": "Governance voting state stored in Rust/WASM and triggered from Solidity.",
        },
        "escrow": {
            "wasm": ContractSpec(
                name="RustEscrow",
                storage=["deposits: mapping(bytes32 => uint256)", "released: mapping(bytes32 => bool)"],
                events=["EscrowDeposited(bytes32 indexed dealId,uint256 amount)", "EscrowReleased(bytes32 indexed dealId,address to)"],
            ),
            "evm": ContractSpec(
                name="SolidityEscrowCaller",
                storage=["escrowTarget: address"],
                events=["CrossVMEscrow(address indexed target,bytes32 indexed dealId,uint256 amount)"],
            ),
            "interface": "IRustEscrow",
            "functions": [
                _fn("deposit", [("dealId", "bytes32"), ("amount", "uint256")]),
                _fn("release", [("dealId", "bytes32"), ("recipient", "address")], "bool"),
                _fn("escrowBalance", [("dealId", "bytes32")], "uint256", "view"),
            ],
            "description": "Escrow accounting and release decisions handled by a WASM contract.",
        },
        "oracle": {
            "wasm": ContractSpec(
                name="RustOracle",
                storage=["prices: mapping(bytes32 => uint256)", "lastUpdated: mapping(bytes32 => uint256)"],
                events=["PriceUpdated(bytes32 indexed feedId,uint256 price,uint256 timestamp)"],
            ),
            "evm": ContractSpec(
                name="SolidityOracleCaller",
                storage=["oracleTarget: address"],
                events=["CrossVMPriceRead(address indexed target,bytes32 indexed feedId,uint256 price)"],
            ),
            "interface": "IRustOracle",
            "functions": [
                _fn("setPrice", [("feedId", "bytes32"), ("price", "uint256")]),
                _fn("getPrice", [("feedId", "bytes32")], "uint256", "view"),
                _fn("lastUpdated", [("feedId", "bytes32")], "uint256", "view"),
            ],
            "description": "Oracle feed storage in Rust/WASM with Solidity reads and updates.",
        },
        "staking": {
            "wasm": ContractSpec(
                name="RustStaking",
                storage=["stakes: mapping(address => uint256)", "rewards: mapping(address => uint256)"],
                events=["Staked(address indexed staker,uint256 amount)", "RewardClaimed(address indexed staker,uint256 reward)"],
            ),
            "evm": ContractSpec(
                name="SolidityStakingCaller",
                storage=["stakingTarget: address"],
                events=["CrossVMStake(address indexed target,address indexed staker,uint256 amount)"],
            ),
            "interface": "IRustStaking",
            "functions": [
                _fn("stake", [("amount", "uint256")]),
                _fn("unstake", [("amount", "uint256")], "bool"),
                _fn("claimRewards", [], "uint256"),
            ],
            "description": "Staking balances and rewards managed by Rust/WASM and invoked by Solidity.",
        },
    }
    definition = definitions[key]

    return ApplicationSpec(
        application_type=key,
        direction=direction,
        contracts={"wasm": definition["wasm"], "evm": definition["evm"]},
        functions=definition["functions"],
        interface_name=str(definition["interface"]),
        description=str(definition["description"]),
    )
