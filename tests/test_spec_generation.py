import unittest

from engine import AgentRequest, run_pipeline


PROMPTS = {
    "erc20": "Build an ERC20 implemented in Rust callable from Solidity",
    "nft": "Build an NFT contract callable from Solidity",
    "voting": "Build a voting contract callable from Solidity",
    "escrow": "Build an escrow contract callable from Solidity",
    "oracle": "Build an oracle price feed callable from Solidity",
    "staking": "Build a staking contract callable from Solidity",
}


EXPECTED = {
    "erc20": ("RustERC20", "SolidityERC20Caller", "mint(address,uint256)"),
    "nft": ("RustNFT", "SolidityNFTCaller", "mintNft(address,uint256)"),
    "voting": ("RustVoting", "SolidityVotingCaller", "vote(uint256)"),
    "escrow": ("RustEscrow", "SolidityEscrowCaller", "deposit(bytes32,uint256)"),
    "oracle": ("RustOracle", "SolidityOracleCaller", "setPrice(bytes32,uint256)"),
    "staking": ("RustStaking", "SolidityStakingCaller", "stake(uint256)"),
}


class SpecGenerationTests(unittest.TestCase):
    def test_prompts_generate_materially_different_artifacts(self):
        results = {
            key: run_pipeline(AgentRequest.from_intent(prompt))
            for key, prompt in PROMPTS.items()
        }

        rust_sources = set()
        solidity_sources = set()
        abi_definitions = set()

        for key, result in results.items():
            wasm_name, evm_name, signature = EXPECTED[key]
            self.assertEqual(result["application_type"], key)
            self.assertEqual(result["contracts"], {"wasm": wasm_name, "evm": evm_name})
            self.assertEqual(result["status"], "SUCCESS")
            self.assertIn(signature, result["artifacts"]["abi_bridge"]["functions"])
            self.assertTrue(result["artifacts"]["wasm_contract"]["storage_model"])
            self.assertTrue(result["artifacts"]["wasm_contract"]["events"])
            rust_sources.add(result["artifacts"]["wasm_contract"]["source"])
            solidity_sources.add(result["artifacts"]["evm_contract"]["source"])
            abi_definitions.add(result["artifacts"]["abi_bridge"]["abi"])

        self.assertEqual(len(rust_sources), len(PROMPTS))
        self.assertEqual(len(solidity_sources), len(PROMPTS))
        self.assertEqual(len(abi_definitions), len(PROMPTS))


if __name__ == "__main__":
    unittest.main()
