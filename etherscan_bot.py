#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import requests
import time
from datetime import datetime
import logging
import logging.handlers
from config import DEBUG,ETHERSCAN_TOKEN,TIME_OUT,TIME_OUT_BETWEEN_REPEAT,SQLALCHEMY_DATABASE_URI,LOG_PATH,ETHERSCAN_TOKEN
from config import CHAT_ID,TELEGRAM_TOKEN

from models import Wallets,Incoming, User_wallets, connect_to_db

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(LOG_PATH)

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

def send_message(text):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}'
        res = requests.get(url)
    except:
        logger.exception('send_message')

def update_data(data,wallet,user_id,session):
    try:
        new_amount = 0.0
        logger.info('Found {} transaction for user_id={}'.format(len(data),user_id))
        for d in data:
            # проверяем наш ли кошелек в "to"
            wallet_to = d.get("to")
            if wallet.lower()  == wallet_to.lower() :
                decimal_correct =  10**int(d.get("tokenDecimal"))
                new_amount = new_amount + float(d.get("value"))/decimal_correct
            else:
                # если нет то пропускаем
                pass

        logger.info(f'All ammount {new_amount}')

        inc_amount = 0.0
        inc_rect = session.query(Incoming).filter_by(user_id = user_id, bot=1).all()
        logger.info('Found {} rect in Incoming table for user_id {} and bot=1'.format(len(inc_rect), user_id))
        for r in inc_rect:
            inc_amount = inc_amount + r.amount
        logger.info(f'All ammount in Incoming table {inc_amount}')

        amount = new_amount - inc_amount

        if amount > 0.0001:
            session.add(Incoming(user_id=user_id,wallet=wallet,amount=amount,txhash='txhash',type=0,viewed=0,bot=1,
                                 status=0,created_at=datetime.utcnow(),updated_at=None))
            session.commit()
            message = f'Add to Incoming table: user_id={user_id}, wallet={wallet}, amount={amount}'
            logger.info(message)
            send_message(f'etherscan_bot said: Пользователь {user_id} пополнил баланс на {amount} WTP')
        else:
            message = f'No new transactions: user_id={user_id}, wallet={wallet}'
            logger.info(message)

    except Exception as e:
        logger.exception(e)


def run_etherscan():
    try:

        session = connect_to_db(SQLALCHEMY_DATABASE_URI)
        if session:
            all = session.query(User_wallets).all()
            message = f'~ start repeat, found {len(all)} user wallets'
            logger.info(message)

            for i, r in enumerate(all):
                api_url = f'https://api.etherscan.io/api?module=account&action=tokentx&contractaddress=' \
                          f'0x1680CfdAD75dA2bb56Ded4f36BB9423C86ffa7B7&address={r.wallet}&page=1&offset=100&sort=asc&apikey={ETHERSCAN_TOKEN}'

                try:
                    req = requests.get(api_url)
                except Exception as e:
                    logger.exception(e)

                if req.status_code == 200:
                    # Check for empty response
                    if req.text:
                        data = req.json()
                        status = data.get('status')
                        if status == '1':
                            logger.info(f'~{i + 1}: Found tranzaction for {r.wallet}')
                            update_data(data.get('result'), r.wallet, r.user_id, session)
                        else:
                            logger.info(f'~{i + 1}: Not found tranzaction for {r.wallet}')
                else:
                    logger.info(f'status_code: {req.status_code}')

                time.sleep(TIME_OUT)

            message = f'compleat'
            logger.info(message)
        else:
            logger.error('session not open')
    except:
        logger.exception('run_etherscan')



def main():
    try:
        logger.info('Start etherscan_bot ...')
        while True:
            run_etherscan()
            time.sleep(TIME_OUT_BETWEEN_REPEAT)

    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
