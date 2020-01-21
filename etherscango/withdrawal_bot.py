#!/usr/bin/python3
# -*- coding: utf-8 -*-
from etherscango.models import  Withdrawals, connect_to_db
import logging
import time, os
from Crypto.Cipher import AES
from base64 import b64decode
import json
from web3.auto import w3
from web3 import Web3, HTTPProvider
from config import CHAT_ID


from config import DEBUG,CONTRACT_ADD, TIME_OUT, SQLALCHEMY_DATABASE_URI,LOG_PATH2, ETH_NODE, \
                    OUT_WALLET, OUT_PRIVKEY, ETH_FEE, COLD_WALLET,ABI_FILE_PATH, MASTERPASS,\
                TIME_OUT_AFTER_HTTPERROR_429,LOG_PATH1,TIME_OUT_TRANS_RECEIPT


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


def chek_receipt_transaction(context=None):
    logger = logging.getLogger(__file__)
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
                message = f'All transaction complete'
                logger.info(message)
                if context:
                    context.bot.send_message(chat_id=CHAT_ID, text='withwdawal_bot: '+ message)

                all_trans_compleate = True
            return True

    except:
        logger.exception('chek_receipt_transaction')
    finally:
        session.close()

def send_wtp_tokens(context=None):
    try:
        global out_nonce
        global all_trans_compleate

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

        session = connect_to_db(SQLALCHEMY_DATABASE_URI)

        withdrawals = session.query(Withdrawals).filter(Withdrawals.status == 0).all()

        message  = f'In table Withdrawals found {len(withdrawals)} wallets'
        logger.info(message)
        if context:
            context.bot.send_message(chat_id=CHAT_ID, text='withwdawal_bot: '+ message)

        if len(withdrawals) < 1:
            # нет пожходящих транзакций
            all_trans_compleate = True
            return False

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
                'gasPrice': w3.toWei(ETH_FEE, 'gwei'),
                'nonce': nonce,
            })
            signed_txn = w3.eth.account.signTransaction(txn, private_key=OUT_PRIVKEY)

            try:
                txhash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                # ставим  pending и сохраням txhash
                w.pending = 1
                w.txhash = txhash.hex()
                session.commit()

                message = f'Произведён вывод {w.amount} wtp по адресу {w.wallet}'
                if context:
                    context.bot.send_message(chat_id=CHAT_ID, text='withwdawal_bot: ' + message)


                nonce = nonce +1
            except Exception as e:
                message = f'Error {e}'
                logger.error(message)
                if context:
                    context.bot.send_message(chat_id=CHAT_ID, text='withwdawal_bot: ' + message)

        return True
    except:
        logger.exception('send wtp')
    finally:
        session.close()

def run_withdrawal(context):
    global all_trans_compleate

    message = 'start withdrawal_bot'
    logger.error(message)
    if context:
        context.bot.send_message(chat_id=CHAT_ID, text='withwdawal_bot: ' + message)

    all_trans_compleate = False

    while not all_trans_compleate:
        # отправляем токены
        if send_wtp_tokens(context):
            # ждем
            time.sleep(10)
            # проверяем отправились ли транзакции
            # если  нужно ждем
            # если все отправленые то  all_trans_compleate = False
            # если есто неуспешные то повторяем их
            while not chek_receipt_transaction(context):
                # ждем 10
                time.sleep(10)


def main():
    run_withdrawal()

if __name__ == '__main__':
    main()
