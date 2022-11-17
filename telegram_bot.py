# coding=utf-8

"""Организует работу telegram-бота магазина рыбы."""

import logging
import os
from functools import partial

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

from moltin import Moltin
from telegram_log_handler import TelegramLogsHandler


START, HANDLE_MENU = range(1, 3)

logger = logging.getLogger('fish_shop_bot.logger')


def run_telegram_bot(tg_bot_token, moltin, redis_client):
    """Запускает telegram-бота и организует его работу."""

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    handler = partial(handle_users_reply, moltin=moltin, redis_client=redis_client)
    dispatcher.add_handler(CallbackQueryHandler(handler))
    dispatcher.add_handler(MessageHandler(Filters.text, handler))
    dispatcher.add_handler(CommandHandler('start', handler))
    dispatcher.add_error_handler(handle_error)

    updater.start_polling()
    updater.idle()


def handle_users_reply(update, context, moltin, redis_client):
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
        HANDLE_MENU: handle_menu
    }
    user_state = START if user_reply == '/start' else redis_client.get(chat_id) or START
    state_handler = states_functions[int(user_state)]

    try:
        next_state = state_handler(update, context, moltin)
        redis_client.set(chat_id, next_state)
    except Exception as err:
        print(err)


def handle_start_command(update, context, moltin):
    """Обрабатывает состояние START."""

    update.message.reply_text(text='Привет!')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет! Я бот магазина рыбы!\nНажми клавишу',
        reply_markup=get_keyboard_markup(moltin)
    )
    return HANDLE_MENU


def handle_menu(update, context, moltin):
    """Обрабатывает состояние HANDLE_MENU."""

    if not update.callback_query:
        return START

    update.callback_query.answer()
    product_id = update.callback_query.data
    product_description = moltin.get_product_by_id(product_id)['data']['description']
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=product_description,
    )
    return START


def get_keyboard_markup(moltin):
    """Возвращает встроенную клавиатуру InlineKeyboardMarkup со списком продуктов магазина."""

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in moltin.get_all_products()['data']
        if product['type'] == 'product'
    ]
    return InlineKeyboardMarkup(keyboard)


def handle_error(update, context, error):
    """Обрабатывает возникающие ошибки."""

    logger.warning(f'Update "{update}" вызвал ошибку "{error}"')


def main():
    load_dotenv()
    tg_bot_token = os.environ['TELEGRAM_BOT_TOKEN']

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(tg_bot_token, os.environ['TELEGRAM_MODERATOR_CHAT_ID']))

    moltin = Moltin(os.environ['MOLTIN_CLIENT_ID'], os.environ['MOLTIN_CLIENT_SECRET'])
    redis_client = redis.StrictRedis(
        host=os.environ['REDIS_DB_HOST'],
        port=os.environ['REDIS_DB_PORT'],
        password=os.environ['REDIS_DB_PASSWORD'],
        decode_responses=True
    )
    run_telegram_bot(tg_bot_token, moltin, redis_client)


if __name__ == '__main__':
    main()
