#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
from web3.auto import w3
from web3 import Web3, HTTPProvider, IPCProvider
import requests

from config import CONTRACT_ADD, ETH_NODE, COLD_WALLET,ABI_FILE_PATH
from config import TELEGRAM_TOKEN, CHAT_ID

logger = logging.getLogger(__file__)


w3 = Web3(HTTPProvider(ETH_NODE))

def send_message(text):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}'
        res = requests.get(url)
    except:
        logger.exception('send_message')

def get_cold_walet_balance():
    try:
        contract_address = Web3.toChecksumAddress(CONTRACT_ADD)

        contract_abi = json.loads(open(ABI_FILE_PATH, "r").read())
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        decimal = contract.functions.decimals().call()

        token_balance = contract.functions.balanceOf(Web3.toChecksumAddress(COLD_WALLET)).call()
        send_message(f'get_cold_wallet_balance seid: Баланс холодного кошелька {token_balance//10**decimal} WTP')

    except Exception as e:
        logger.exception(e)
        send_message(f'get_cold_wallet_balance seid: error {e}')


if __name__ == '__main__':
    get_cold_walet_balance()

