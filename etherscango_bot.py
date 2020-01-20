#!/usr/bin/python3
import os
import sys
from threading import Thread
import logging
import random
import time
import os
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler,CallbackContext)
from telegram import Update
from config import CHAT_ID,TOKEN,YOUR_TELEGRAM_ALIAS,START_INCOMING_BOT,START_WITHDRAWAL_BOT



START, START_TOKENSEND, GETJOB = range(3)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text('Привет,')
    update.message.reply_text('Для запуска tokensend_bot отправьте команду /tokensend')
    update.message.reply_text('Для просмотра очереди задач отправьте команду /jobstat')
    update.message.reply_text('Для перезапуска бота  отправьте команду /restart')
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text('Пока')
    return ConversationHandler.END

def callback_tokensend_bot(context: CallbackContext):
    context.bot.send_message(chat_id=CHAT_ID,
                             text='tokensend_bot start')
    # send_wtp_tokens()
    time.sleep(5)
    context.bot.send_message(chat_id=CHAT_ID,
                             text='tokensend_bot отработал успешно')

def start_tokensend_bot(update, context):
    update.message.reply_text('Добавляем  tokensend_bot  в очередь задач...')
    j = context.job_queue
    j.run_once(callback_tokensend_bot, when=1)
    return ConversationHandler.END

def getjob(update,context):
    update.message.reply_text('Hi you see job runing ..')
    j = context.job_queue.jobs()
    if len(j)>0:
        update.message.reply_text(f'Count job runing {len(j)}:')
        for i in j:
            update.message.reply_text(f'job name:{i.name}')
    else:
        update.message.reply_text('Not runing jobs')
    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


#------ job ----
def callback_withdrawal(context: CallbackContext):
    j = context.job_queue.jobs()
    context.bot.send_message(chat_id=CHAT_ID,
                             text='withdrawal: start')
    t = random.randint(1, 12)
    context.bot.send_message(chat_id=CHAT_ID,
                             text=f'withdrawal: run {t} c')
    time.sleep(t)

    t =random.randint(2,13)
    time.sleep(t)
    context.bot.send_message(chat_id=CHAT_ID,
                             text=f'withdrawal: stop {t} c')


def callback_etherscan(context: CallbackContext):
    context.bot.send_message(chat_id=CHAT_ID,
                             text='callback_etherscan start')
    time.sleep(random.randint(10,20))
    context.bot.send_message(chat_id=CHAT_ID,
                             text='callback_etherscan run')
    time.sleep(random.randint(20,30))
    context.bot.send_message(chat_id=CHAT_ID,
                             text='callback_etherscan stop')

def callback_etherscan1(context: CallbackContext):
    context.bot.send_message(chat_id=CHAT_ID,
                             text='callback_etherscan start')
    time.sleep(random.randint(10,20))
    context.bot.send_message(chat_id=CHAT_ID,
                             text='callback_etherscan run')
    time.sleep(random.randint(20,30))
    context.bot.send_message(chat_id=CHAT_ID,
                             text='callback_etherscan stop')

def main():
    updater = Updater(TOKEN, use_context=True)
    job_queue = updater.job_queue

    # Запускаем нужных ботов в очередь задач
    if START_INCOMING_BOT:
        logger.info('Add incoming_bot to job queue ')
        job_queue.run_repeating(callback_etherscan, interval=60*3, first=0)
    if START_WITHDRAWAL_BOT:
        logger.info('Add withdrawal_bot to job queue ')
        job_queue.run_repeating(callback_withdrawal, interval=60*5, first=0)

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

    #-------bot's service handlers
    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update,context ):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()
        update.message.reply_text('Bot had been restarted!')

    restart_handler = ConversationHandler(
        entry_points=[CommandHandler('restart', restart)],
        states={
            GETJOB: [MessageHandler(Filters.text, restart)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(restart_handler)
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
