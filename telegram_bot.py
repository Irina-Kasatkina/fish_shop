# coding=utf-8

"""Организует работу telegram-бота магазина рыбы."""

import logging
import os
from functools import partial

import redis
from dotenv import load_dotenv
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

from moltin import Moltin
from telegram_log_handler import TelegramLogsHandler


START, ECHO = range(1, 3)

logger = logging.getLogger('fish_shop_bot.logger')


def run_telegram_bot(tg_bot_token, redis_client):
    """Запускает telegram-бота и организует его работу."""

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(partial(handle_users_reply, redis_client=redis_client)))
    dispatcher.add_handler(MessageHandler(Filters.text, partial(handle_users_reply, redis_client=redis_client)))
    dispatcher.add_handler(CommandHandler('start', partial(handle_users_reply, redis_client=redis_client)))
    dispatcher.add_error_handler(handle_error)

    updater.start_polling()
    updater.idle()


def handle_users_reply(update, context, redis_client):
    """Функция, обрабатывающая все действия пользователя."""

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    states_functions = {
        START: handle_start_command,
        ECHO: handle_echo
    }
    print(states_functions)
    user_state = START if user_reply == '/start' else redis_client.get(chat_id) or START
    state_handler = states_functions[int(user_state)]

    try:
        next_state = state_handler(update, context)
        redis_client.set(chat_id, next_state)
    except Exception as err:
        print(err)


def handle_start_command(update, context):
    """Обрабатывает состояние START."""

    update.message.reply_text(text='Привет!')
    return ECHO


def handle_echo(update, context):
    """Обрабатывает состояние ECHO."""

    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return ECHO

def handle_error(update, context, error):
    """Обрабатывает возникающие ошибки."""

    logger.warning(f'Update "{update}" вызвал ошибку "{error}"')


def main():
    load_dotenv()
    tg_bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    tg_moderator_chat_id = os.environ['TELEGRAM_MODERATOR_CHAT_ID']

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(tg_bot_token, tg_moderator_chat_id))

    redis_client = redis.StrictRedis(
        host=os.environ['REDIS_DB_HOST'],
        port=os.environ['REDIS_DB_PORT'],
        password=os.environ['REDIS_DB_PASSWORD'],
        decode_responses=True
    )

    run_telegram_bot(tg_bot_token, redis_client)

    # moltin = Moltin(os.environ['MOLTIN_CLIENT_ID'], os.environ['MOLTIN_CLIENT_SECRET'])


if __name__ == '__main__':
    main()
