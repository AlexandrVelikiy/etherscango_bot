#!/usr/bin/python3
import logging
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler,CallbackContext)

from config import CHAT_ID,TELEGRAM_TOKEN,\
    START_INCOMING_BOT,START_WITHDRAWAL_BOT,INTERVAL_INCOMING_BOT, INTERVAL_WITHDRAWAL_BOT

# импортируем ботов
from etherscango.etherscan_bot import run_etherscan
from etherscango.withdrawal_bot import run_withdrawal
from etherscango.tokensend_bot import send_wtp_tokens


START, START_TOKENSEND, GETJOB = range(3)


logging.basicConfig(format='[LINE:%(lineno)d]#%(asctime)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__file__)


def start(update, context):
    update.message.reply_text('Привет, бот запустит 2 задачи автоматически')
    update.message.reply_text('Для запуска tokensend_bot отправьте команду /tokensend')
    update.message.reply_text('Для просмотра очереди задач отправьте команду /jobstat')
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text('Пока')
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
    context.bot.send_message(chat_id=CHAT_ID, text='~bot: start tokensend_bot')
    send_wtp_tokens(context)
    context.bot.send_message(chat_id=CHAT_ID,
                             text='~bot: stop tokensend_bot')


def callback_withdrawal(context: CallbackContext):
    context.bot.send_message(chat_id=CHAT_ID, text='~bot: start withdrawal ...')
    run_withdrawal(context)
    context.bot.send_message(chat_id=CHAT_ID,
                             text=f'~bot: stop withdrawal')


def callback_etherscan(context: CallbackContext):
    context.bot.send_message(chat_id=CHAT_ID,text='~bot: start run_etherscan ...')
    run_etherscan(context)
    context.bot.send_message(chat_id=CHAT_ID,
                             text='~bot: stop run_etherscan')

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    job_queue = updater.job_queue

    # Запускаем нужных ботов в очередь задач
    if START_INCOMING_BOT:
        logger.info('Add incoming_bot to job queue ')
        job_queue.run_repeating(callback_etherscan, interval=INTERVAL_INCOMING_BOT, first=0)
    if START_WITHDRAWAL_BOT:
        logger.info('Add withdrawal_bot to job queue ')
        job_queue.run_repeating(callback_withdrawal, interval=INTERVAL_WITHDRAWAL_BOT, first=0)

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
