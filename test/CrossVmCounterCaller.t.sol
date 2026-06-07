// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {CrossVmCounterCaller} from "../contracts/evm/CrossVmCounterCaller.sol";

contract MockWasmCounter {
    uint256 private value;
    address public owner;
    bool public shouldRevert;

    error MockFailure();

    function increment(uint256 amount) external returns (uint256) {
        if (shouldRevert) revert MockFailure();
        value += amount;
        return value;
    }

    function get() external view returns (uint256) {
        return value;
    }

    function setOwner(address newOwner) external returns (bool) {
        if (shouldRevert) revert MockFailure();
        owner = newOwner;
        return true;
    }

    function setShouldRevert(bool value_) external {
        shouldRevert = value_;
    }
}

contract CrossVmCounterCallerTest is Test {
    MockWasmCounter internal wasm;
    CrossVmCounterCaller internal caller;

    function setUp() public {
        wasm = new MockWasmCounter();
        caller = new CrossVmCounterCaller(address(wasm));
    }

    function testConstructorRejectsZeroAddress() public {
        vm.expectRevert(CrossVmCounterCaller.ZeroWasmAddress.selector);
        new CrossVmCounterCaller(address(0));
    }

    function testIncrementViaWasm() public {
        vm.expectEmit(true, true, false, false);
        emit CrossVmCounterCaller.CrossVMCallSuccess(
            address(wasm),
            MockWasmCounter.increment.selector,
            ""
        );

        uint256 value = caller.incrementViaWasm(7);

        assertEq(value, 7);
        assertEq(caller.readWasmCounter(), 7);
    }

    function testSetWasmOwner() public {
        bool changed = caller.setWasmOwner(address(0xBEEF));

        assertTrue(changed);
        assertEq(wasm.owner(), address(0xBEEF));
    }

    function testBubblesCrossVmFailure() public {
        wasm.setShouldRevert(true);

        vm.expectRevert(CrossVmCounterCaller.CrossVmCallFailed.selector);
        caller.incrementViaWasm(1);
    }
}
