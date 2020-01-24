#!/usr/bin/python3
# -*- coding: utf-8 -*-
from models import  Withdrawals, connect_to_db
import logging
import time, os
from Crypto.Cipher import AES
from base64 import b64decode
import json
from web3.auto import w3
from web3 import Web3, HTTPProvider
import requests



from config import DEBUG,CONTRACT_ADD, TIME_OUT, SQLALCHEMY_DATABASE_URI,LOG_PATH, ETH_NODE, \
                    OUT_WALLET, OUT_PRIVKEY, ETH_FEE_WD, COLD_WALLET,ABI_FILE_PATH, MASTERPASS,TIME_OUT_BETWEEN_REPEAT, TIME_OUT_TRANS_RECEIPT, LOG_PATH2


from config import TELEGRAM_TOKEN,CHAT_ID

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(LOG_PATH2)
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
if DEBUG:
    formatter = logging.Formatter('[LINE:%(lineno)d]#%(asctime)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
else:
    formatter = logging.Formatter('%(asctime)s: %(message)s')

fh.setFormatter(formatter)
logger.addHandler(fh)

out_wallet=Web3.toChecksumAddress(OUT_WALLET)
out_nonce=0
w3 = Web3(HTTPProvider(ETH_NODE))
hashes = []
pending = []
all_trans_compleate = False

def send_message(text):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}'
        res = requests.get(url)
    except:
        logger.exception('send_message')

def str_to_bytes(data):
    u_type = type(b''.decode('utf8'))
    if isinstance(data, u_type):
        return data.encode('utf8')
    return data

def _pad(s):
    bs=16
    return s + (bs - len(s) % bs) * str_to_bytes(chr(bs - len(s) % bs))

def _unpad(s):
    return s[:-ord(s[len(s)-1:])]

def decrypt(enc, password):
    salt, iv, payload = b64decode(enc).decode().split("-")
    key = salt+password
    enc = b64decode(payload)
    cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
    data=cipher.decrypt(enc)
    return _unpad(data.decode())


def chek_receipt_transaction():
    global all_trans_compleate
    try:
        session = connect_to_db(SQLALCHEMY_DATABASE_URI)
        pendingtrans = session.query(Withdrawals).filter(Withdrawals.pending == 1).all()
        logger.info(f'Found {len(pendingtrans)} transactions')

        for pend_tr in pendingtrans:
            try:
                r = w3.eth.getTransactionReceipt(pend_tr.txhash)
                if not r:
                    # pending ...
                    continue
                else:
                    status = r['status']
                    if status == 1:
                        # транзакция прошла
                        pend_tr.pending = 0
                        pend_tr.status = 1
                        pend_tr.txhash = ''
                        session.commit()
                        send_message(f'withdrawal_bot said: Произведён вывод {pend_tr.amount} wtp по адресу {pend_tr.wallet}')
                    else:
                        # транзакция неуспешна
                        pend_tr.pending = 0
                        pend_tr.status = 0
                        pend_tr.txhash = 'fail'
                        session.commit()

            except Exception as e:
                # транзакция ненайдена
                print(e)

        # проверяме если в базе есть тразакции которые ожидают завершения
        pendingtrans = session.query(Withdrawals).filter(Withdrawals.pending == 1).all()
        if len(pendingtrans) > 0:
            logger.info(f'Found {len(pendingtrans)} pendingt transaction')
            return False
        else:
            # проверяем есть ли транзакции которые не прошли - txhash = fail
            failtrans = session.query(Withdrawals).filter(Withdrawals.txhash == 'fail').all()
            if len(failtrans) > 0:
                logger.info(f'{len(failtrans)} transaction fail, repeat them')
            else:
                logger.info(f'All transaction complete')
                all_trans_compleate = True
            return True

    except Exception as e:
        logger.exception('chek_receipt_transaction')
    finally:
        session.close()

def send_wtp_tokens():
    global out_nonce
    try:
        session = connect_to_db(SQLALCHEMY_DATABASE_URI)

        out_nonce = w3.eth.getTransactionCount(out_wallet)
        logger.info(f'out_wallet nouce {out_nonce}')

        contract_address=Web3.toChecksumAddress(CONTRACT_ADD)

        try:
            contract_abi = json.loads(open(ABI_FILE_PATH,"r").read())
        except:
            logger.info(f'ABI file {ABI_FILE_PATH} not found')
            return False

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        decimal = contract.functions.decimals().call()
        out_wallet_balance = contract.functions.balanceOf(Web3.toChecksumAddress(out_wallet)).call()
        eth_balance = w3.eth.getBalance(Web3.toChecksumAddress(out_wallet))

        logger.info(f'Out wallet balance {out_wallet_balance}')
        logger.info(f"Eth balance: {eth_balance}")

        withdrawals = session.query(Withdrawals).filter(Withdrawals.status == 0).all()
        logger.info(f'In table Withdrawals found {len(withdrawals)} wallets')
        nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(out_wallet))

        for i, w in enumerate(withdrawals):
            time.sleep(TIME_OUT)

            logger.info(f'Send {w.amount} WTP tokens to {w.wallet} ...')
            txn = contract.functions.transfer(
                Web3.toChecksumAddress(w.wallet),
                int(w.amount*10**decimal),
            ).buildTransaction({
                'chainId': 1,
                'gas': 100000,
                'gasPrice': w3.toWei(ETH_FEE_WD, 'gwei'),
                'nonce': nonce,
            })
            signed_txn = w3.eth.account.signTransaction(txn, private_key=OUT_PRIVKEY)

            try:
                txhash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                # ставим  pending и сохраням txhash
                w.pending = 1
                w.txhash = txhash.hex()
                session.commit()

                #send_message(f'withdrawal_bot said: Произведён вывод {w.amount} wtp по адресу {w.wallet}')

                nonce = nonce +1
            except Exception as e:
                message = f'Error {e}'
                logger.error(message)

    except Exception as e:
        logger.exception('send wtp')
        send_message(f'withdrawal_bot said: {e}')
    finally:
        session.close()

def withdrawal():
    global all_trans_compleate
    try:
        while True:
            all_trans_compleate = False
            while not all_trans_compleate:
                # отправляем токены
                send_wtp_tokens()
                # ждем
                time.sleep(TIME_OUT_TRANS_RECEIPT)
                # проверяем отправились ли транзакции
                # если  нужно ждем
                # если все отправленые то  all_trans_compleate = False
                # если есто неуспешные то повторяем их
                while not chek_receipt_transaction():
                    # ждем 10
                    time.sleep(TIME_OUT_TRANS_RECEIPT)

            time.sleep(TIME_OUT_BETWEEN_REPEAT)
    except:
        logger.exception('withdrawal')

def main():
    withdrawal()


if __name__ == '__main__':
    main()