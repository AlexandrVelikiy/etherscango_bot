# -*- coding: utf-8 -*-

MASTERPASS="JL5rslduQE3c38od"
ETH_NODE = 'https://mainnet.infura.io/v3/579dff22939f472199392c37f11db0a5'#'https://mainnet.infura.io/ca7647192cca4daf8193b9bae3921910'

ABI_FILE_PATH = '/home/alex/proj/etherscango_bot/json.abi'

CONTRACT_ADD = '0x1680CfdAD75dA2bb56Ded4f36BB9423C86ffa7B7'
COLD_WALLET = '0x525c9e7c5cec37adfcddf2c70eea25dfa6004693'
OUT_WALLET = '0x4A8dd2Dc8407C98221959fFBbc13b18321b9019e'#'0x85567eb0322d392b1E3946fBAbC42f42617381b4'
OUT_PRIVKEY='5B35050F0E64757E3FC0C6DCB6C0F1A5D7EBC8DE11E39CD9FA89C2A8EA4F446E'

ETH_FEE = 3
ETH_FEE_WD = 5 # для withdrawal bot

DEBUG = True
ETHERSCAN_TOKEN = '5UZG48NFB3PF1SCU83V2I9UXEHKHSRQYFT'
TIME_OUT = 0.25 # ограничим не более 4-х запросов в секунду
TOKENSEND_TIME_OUT = 1
TIME_OUT_AFTER_HTTPERROR_429 = 45 # пауза после ошибки
TIME_OUT_BETWEEN_REPEAT = 60 # тайм аут между повторным и запусками withdrawal и etherscan
TIME_OUT_AFTER_REPLAY =  60 # пауза между поторными запросами на подтверждение транзакции для withdrawal_bot
# для withdrawel
TIME_OUT_TRANS_RECEIPT = 30
# таймаут для запроса баланса холожного кошелька
TIME_OUT_GET_COLD_BALANC = 30

# доступ к базе
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://alex:passw0rd159@localhost/wtp_mining'

#путь к лог файлуам
LOG_PATH = '/home/alex/proj/etherscango_bot/log/etherscan_bot.log'
LOG_PATH1 = '/home/alex/proj/etherscango_bot/log/tokensend_bot.log'
LOG_PATH2 = '/home/alex/proj/etherscango_bot/log/withdrawal_bot.log'


#  Для телеграм бота
TELEGRAM_TOKEN = "926797988:AAEvBF2YuiINBUK7PSZ4OSijwbOi9v1rEOw"
CHAT_ID = '505067837'
YOUR_TELEGRAM_ALIAS ='@my_coffee_factory_bot'

# Выбераем какие боты будут запускаться в JobQueue при старте
START_INCOMING_BOT = True
INTERVAL_INCOMING_BOT = 60*5 # пауза меж запусками
START_WITHDRAWAL_BOT = True
INTERVAL_WITHDRAWAL_BOT =  60*6

#Еслии True  то шлем в телеграм сообщения о запуске остановке ботов и т.п.
SEND_DEBAG_MESSAGE = True # пока не работает