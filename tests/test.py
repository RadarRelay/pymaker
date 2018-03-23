# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
from web3 import Web3, EthereumTesterProvider

from pymaker import Address, eth_transfer
from pymaker.numeric import Wad
from pymaker.token import DSToken
from pymaker.util import synchronize, eth_balance


class TestTransact:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.second_address = Address(self.web3.eth.accounts[1])
        self.third_address = Address(self.web3.eth.accounts[2])
        self.token = DSToken.deploy(self.web3, 'ABC')
        self.token.mint(Wad(1000000)).transact()

    def test_default_gas(self):
        # when
        receipt = self.token.transfer(self.second_address, Wad(500)).transact()

        # then
        # [token transfer costs ~50k gas, we should add a 100k buffer by default which puts in the (100k, 200k) range]
        assert 100000 <= self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] <= 200000

    def test_default_gas_async(self):
        # when
        receipt = synchronize([self.token.transfer(self.second_address, Wad(500)).transact_async()])[0]

        # then
        # [token transfer costs ~50k gas, we should add a 100k buffer by default which puts in the (100k, 200k) range]
        assert 100000 <= self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] <= 200000

    def test_custom_gas(self):
        # when
        receipt = self.token.transfer(self.second_address, Wad(500)).transact(gas=129995)

        # then
        assert self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] == 129995

    def test_custom_gas_async(self):
        # when
        receipt = synchronize([self.token.transfer(self.second_address, Wad(500)).transact_async(gas=129995)])[0]

        # then
        assert self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] == 129995

    def test_custom_gas_buffer(self):
        # when
        receipt = self.token.transfer(self.second_address, Wad(500)).transact(gas_buffer=3000000)

        # then
        assert self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] > 3000000

    def test_gas_and_gas_buffer_not_allowed_at_the_same_time(self):
        # expect
        with pytest.raises(Exception):
            self.token.transfer(self.second_address, Wad(500)).transact(gas=129995, gas_buffer=3000000)

    def test_gas_and_gas_buffer_not_allowed_at_the_same_time_async(self):
        # expect
        with pytest.raises(Exception):
            synchronize([self.token.transfer(self.second_address, Wad(500)).transact_async(gas=129995,
                                                                                           gas_buffer=3000000)])

    def test_custom_from_address(self):
        # given
        self.token.transfer(self.second_address, Wad(self.token.balance_of(self.our_address))).transact()

        # when
        receipt = self.token.transfer(self.our_address, Wad(250)).transact(from_address=self.second_address)

        # then
        assert Address(self.web3.eth.getTransaction(receipt.transaction_hash)['from']) == self.second_address

    def test_eth_transfer(self):
        # given
        assert eth_balance(self.web3, self.second_address) == Wad.from_number(1000000)

        # when
        eth_transfer(self.web3, self.second_address, Wad.from_number(1.5)).transact()

        # then
        assert eth_balance(self.web3, self.second_address) == Wad.from_number(1000000) + Wad.from_number(1.5)

    def test_eth_transfer_from_other_account(self):
        # given
        assert eth_balance(self.web3, self.second_address) == Wad.from_number(1000000)
        assert eth_balance(self.web3, self.third_address) == Wad.from_number(1000000)

        # when
        eth_transfer(self.web3, self.third_address, Wad.from_number(1.5)).transact(from_address=self.second_address)

        # then
        assert eth_balance(self.web3, self.second_address) < Wad.from_number(1000000)
        assert eth_balance(self.web3, self.third_address) == Wad.from_number(1000000) + Wad.from_number(1.5)
