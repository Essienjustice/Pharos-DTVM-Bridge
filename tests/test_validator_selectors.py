import unittest

from web3 import Web3

from engine.generator import Generator
from engine.planner import Planner
from engine.validator import validate_artifacts


def selector(signature: str) -> str:
    return "0x" + Web3.keccak(text=signature).hex()[:8]


class ValidatorSelectorTests(unittest.TestCase):
    def test_mint_uint256_selector(self):
        self.assertEqual(selector("mint(uint256)"), "0xa0712d68")

    def test_balance_of_selector(self):
        self.assertEqual(selector("balanceOf(address)"), "0x70a08231")

    def test_transfer_selector(self):
        self.assertEqual(selector("transfer(address,uint256)"), "0xa9059cbb")

    def test_selector_mismatch_detected(self):
        plan = Planner().plan("ERC20 token in Rust callable from Solidity")
        artifacts = Generator().generate(plan)
        bad_selectors = [
            {"signature": "Mint(uint256)", "selector": selector("Mint(uint256)")}
        ]
        artifacts.abi_bridge["selectors"] = bad_selectors
        report = validate_artifacts(plan, artifacts)
        self.assertEqual(report.status, "FAILURE")

    def _assert_no_unresolved_vars(self, intent: str):
        plan = Planner().plan(intent)
        result = Generator().generate(plan)
        self.assertNotIn("{", result.rust_source)
        self.assertNotIn("{", result.solidity_source)

    def test_no_unresolved_vars_erc20(self):
        self._assert_no_unresolved_vars("ERC20 token in Rust callable from Solidity")

    def test_no_unresolved_vars_nft(self):
        self._assert_no_unresolved_vars("NFT in Rust with Solidity minting interface")

    def test_no_unresolved_vars_staking(self):
        self._assert_no_unresolved_vars("Staking: Rust computes rewards, Solidity claims")

    def test_no_unresolved_vars_oracle(self):
        self._assert_no_unresolved_vars("Oracle: Rust stores prices, Solidity reads")


if __name__ == "__main__":
    unittest.main()
