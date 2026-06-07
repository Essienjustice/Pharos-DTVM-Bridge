// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script} from "forge-std/Script.sol";
import {CrossVmCounterCaller} from "../contracts/evm/CrossVmCounterCaller.sol";

contract DeployCounterCaller is Script {
    function run(address wasmCounter) external returns (CrossVmCounterCaller deployed) {
        vm.startBroadcast();
        deployed = new CrossVmCounterCaller(wasmCounter);
        vm.stopBroadcast();
    }
}
