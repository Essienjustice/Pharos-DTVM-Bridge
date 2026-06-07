import json
import subprocess
import sys
import unittest


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "cli.py", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(completed.stdout)


class PipelineE2ETests(unittest.TestCase):
    def test_erc20_exits_zero(self):
        self.assertEqual(run_cli("ERC20").returncode, 0)

    def test_output_is_valid_json(self):
        data = parse_stdout_json(run_cli("ERC20"))
        self.assertEqual(data["status"], "SUCCESS")

    def test_nft_archetype_detected(self):
        data = parse_stdout_json(run_cli("NFT contract in Rust with Solidity minting"))
        self.assertEqual(data["application_type"], "nft")

    def test_voting_archetype_detected(self):
        data = parse_stdout_json(run_cli("Build a voting contract callable from Solidity"))
        self.assertEqual(data["application_type"].lower(), "voting")

    def test_wasm_revert_has_decoded_message(self):
        data = parse_stdout_json(run_cli("ERC20", "--simulate", "wasm_revert"))
        self.assertIn("ABI-decoded", data["detail"])

    def test_abi_mismatch_failure_class(self):
        data = parse_stdout_json(run_cli("ERC20", "--simulate", "abi_mismatch"))
        self.assertEqual(data["failure_class"], "ABI_MISMATCH")

    def test_deploy_order_error_failure_class(self):
        data = parse_stdout_json(run_cli("ERC20", "--simulate", "deploy_order_error"))
        self.assertEqual(data["failure_class"], "DEPLOY_ORDER_ERROR")

    def test_rust_has_cross_vm_pattern(self):
        data = parse_stdout_json(run_cli("Oracle: Rust stores prices, Solidity reads"))
        rust_source = data["artifacts"]["wasm_contract"]["source"]
        self.assertTrue("sol!" in rust_source or "self.vm()" in rust_source)

    def test_solidity_has_try_catch(self):
        data = parse_stdout_json(run_cli("Staking: Rust computes rewards, Solidity claims"))
        self.assertIn("try ", data["artifacts"]["evm_contract"]["source"])

    def test_dtvm_reference_in_output(self):
        data = parse_stdout_json(run_cli("ERC20"))
        self.assertIn("paper", data["dtvm_reference"])

    def test_no_legacy_vm_name_in_output(self):
        completed = run_cli("ERC20")
        forbidden = "do" + "ra vm"
        self.assertNotIn(forbidden, completed.stdout.lower())

    def test_compilation_mode_is_mock(self):
        data = parse_stdout_json(run_cli("ERC20"))
        self.assertEqual(data["compilation"]["mode"], "mock")


if __name__ == "__main__":
    unittest.main()
