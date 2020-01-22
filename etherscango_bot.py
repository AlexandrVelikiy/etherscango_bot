#!/usr/bin/python3
import logging
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler,CallbackContext)

from config import CHAT_ID,TELEGRAM_TOKEN, TIME_OUT_GET_COLD_BALANC

# импортируем ботов
from etherscango.tokensend_bot import send_wtp_tokens
from etherscango.get_balance_cold_wallet import get_cold_walet_balance


START, START_TOKENSEND, GETJOB, GETBAL = range(4)


logging.basicConfig(format='[LINE:%(lineno)d]#%(asctime)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__file__)


def start(update, context):
    update.message.reply_text('Привет!')
    update.message.reply_text('Для запуска tokensend_bot отправьте команду /tokensend')
    update.message.reply_text('Для запуска просмотра баланса холодного кошелька отправьте команду /getbalabce')
    update.message.reply_text('Для просмотра очереди задач отправьте команду /jobstat')
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text('Пока')
    return ConversationHandler.END

def start_getbalance_bot(update, context):
    update.message.reply_text('Добавляем  get_cold_wallet_balance  в очередь задач...')
    j = context.job_queue
    # проверям есть ли такое задание уже в очереди
    jobs = j.jobs()

    new_job = True
    if len(jobs) > 0:
        for i in jobs:
            if i.name == 'get_cold_walet_balance':
                update.message.reply_text('Задание get_cold_walet_balance уже есть в очередь')
                new_job = False

    if new_job:
        j.run_once(callback_get_cold_walet_balance, when=1)
        update.message.reply_text('Задание get_cold_walet_balance добавлено в очередь')
    return ConversationHandler.END

def start_tokensend_bot(update, context):
    update.message.reply_text('Добавляем  tokensend_bot  в очередь задач...')
    j = context.job_queue
    # проверям есть ли такое задание уже в очереди
    jobs =j.jobs()

    new_job = True
    if len(jobs) > 0:
        for i in jobs:
            if i.name == 'callback_tokensend_bot':
                update.message.reply_text('Задание tokensend_bot уже есть в очередь')
                new_job = False

    if new_job:
        j.run_once(callback_tokensend_bot, when=1)
        update.message.reply_text('Задание tokensend_bot добавлено в очередь')
    return ConversationHandler.END

def getjob(update,context):
    update.message.reply_text('Список заданий в очереди:')
    j = context.job_queue.jobs()
    if len(j)>0:
        update.message.reply_text(f'Количество заданий {len(j)}:')
        for i in j:
            update.message.reply_text(f'Имя: {i.name}, интервал запуска: {i.interval_seconds} с')
    else:
        update.message.reply_text('Нет заданий в очереди')
    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


#------ jobs ----
def callback_tokensend_bot(context: CallbackContext):
    send_wtp_tokens()
    # запускаем запрос баланса холодного кошелька через интервал  TIME_OUT_GET_COLD_BALANC
    j = context.job_queue
    j.run_once(callback_get_cold_walet_balance, TIME_OUT_GET_COLD_BALANC)


def callback_get_cold_walet_balance(context: CallbackContext):
    get_cold_walet_balance()

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    job_queue = updater.job_queue

    dp = updater.dispatcher
    start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [MessageHandler(Filters.text, start)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(start_handler)

    tokensend_handler = ConversationHandler(
        entry_points=[CommandHandler('tokensend', start_tokensend_bot)],
        states={
            GETJOB: [MessageHandler(Filters.text, start_tokensend_bot)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(tokensend_handler)

    get_balance_handler = ConversationHandler(
        entry_points=[CommandHandler('getbalabce', start_getbalance_bot)],
        states={
            GETBAL: [MessageHandler(Filters.text, start_getbalance_bot)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(get_balance_handler)


    jobstat_handler = ConversationHandler(
        entry_points=[CommandHandler('jobstat', getjob)],
        states={
            GETJOB: [MessageHandler(Filters.text, getjob)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(jobstat_handler)

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
