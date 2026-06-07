// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IWasmCounter} from "./interfaces/IWasmCounter.sol";

contract CrossVmCounterCaller {
    error ZeroWasmAddress();
    error CrossVmCallFailed(bytes reason);

    event WasmTargetUpdated(address indexed previousTarget, address indexed newTarget);
    event CrossVMCallSuccess(address indexed wasmTarget, bytes4 indexed selector, bytes returnData);
    event CrossVMCallFailed(address indexed wasmTarget, bytes4 indexed selector, bytes reason);

    IWasmCounter public immutable wasmCounter;

    constructor(address wasmCounter_) {
        if (wasmCounter_ == address(0)) revert ZeroWasmAddress();
        wasmCounter = IWasmCounter(wasmCounter_);
        emit WasmTargetUpdated(address(0), wasmCounter_);
    }

    function incrementViaWasm(uint256 amount) external returns (uint256 value) {
        bytes memory data = abi.encodeCall(IWasmCounter.increment, (amount));
        (bool ok, bytes memory ret) = address(wasmCounter).call(data);

        if (!ok) {
            emit CrossVMCallFailed(address(wasmCounter), IWasmCounter.increment.selector, ret);
            revert CrossVmCallFailed(ret);
        }

        value = abi.decode(ret, (uint256));
        emit CrossVMCallSuccess(address(wasmCounter), IWasmCounter.increment.selector, ret);
    }

    function readWasmCounter() external view returns (uint256) {
        return wasmCounter.get();
    }

    function setWasmOwner(address newOwner) external returns (bool changed) {
        bytes memory data = abi.encodeCall(IWasmCounter.setOwner, (newOwner));
        (bool ok, bytes memory ret) = address(wasmCounter).call(data);

        if (!ok) {
            emit CrossVMCallFailed(address(wasmCounter), IWasmCounter.setOwner.selector, ret);
            revert CrossVmCallFailed(ret);
        }

        changed = abi.decode(ret, (bool));
        emit CrossVMCallSuccess(address(wasmCounter), IWasmCounter.setOwner.selector, ret);
    }
}
