#![cfg_attr(not(feature = "export-abi"), no_main)]

extern crate alloc;

use stylus_sdk::{
    alloy_primitives::{Address, U256},
    alloy_sol_types::{sol, SolError},
    prelude::*,
};

sol! {
    interface IWasmCounter {
        function increment(uint256 amount) external returns (uint256);
        function get() external view returns (uint256);
        function setOwner(address newOwner) external returns (bool);
    }

    error NotOwner(address caller, address owner);
    error ZeroAddress();
}

sol_storage! {
    #[entrypoint]
    pub struct WasmCounter {
        uint256 value;
        address owner;
    }
}

#[public]
impl WasmCounter {
    pub fn increment(&mut self, amount: U256) -> U256 {
        let next = self.value.get() + amount;
        self.value.set(next);
        next
    }

    pub fn get(&self) -> U256 {
        self.value.get()
    }

    pub fn set_owner(&mut self, new_owner: Address) -> Result<bool, Vec<u8>> {
        if new_owner == Address::ZERO {
            return Err(ZeroAddress {}.abi_encode());
        }

        let caller = self.vm().msg_sender();
        let owner = self.owner.get();

        if owner != Address::ZERO && caller != owner {
            return Err(NotOwner { caller, owner }.abi_encode());
        }

        self.owner.set(new_owner);
        Ok(true)
    }
}
