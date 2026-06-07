// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IWasmCounter {
    function increment(uint256 amount) external returns (uint256);
    function get() external view returns (uint256);
    function setOwner(address newOwner) external returns (bool);
}
