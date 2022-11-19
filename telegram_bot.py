# coding=utf-8

"""Organize the work of the fish shop telegram bot."""

import logging
import os
import re
from contextlib import suppress
from functools import partial

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

from moltin import Moltin
from telegram_log_handler import TelegramLogsHandler


START, HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART, WAITING_EMAIL = range(1, 6)

logger = logging.getLogger('fish_shop_bot.logger')


def run_telegram_bot(tg_bot_token, moltin, redis_client):
    """Launch a telegram bot and organize its work."""

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    handler = partial(handle_users_reply, moltin=moltin, redis_client=redis_client)
    dispatcher.add_handler(CallbackQueryHandler(handler))
    dispatcher.add_handler(MessageHandler(Filters.text, handler))
    dispatcher.add_handler(CommandHandler('start', handler))
    # dispatcher.add_error_handler(handle_error)

    updater.start_polling()
    updater.idle()


def handle_users_reply(update, context, moltin, redis_client):
    """Handle all user actions."""

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
        HANDLE_MENU: handle_main_menu,
        HANDLE_DESCRIPTION: handle_description_menu,
        HANDLE_CART: handle_cart_menu,
        WAITING_EMAIL: handle_email_message
    }
    user_state = START if user_reply == '/start' else redis_client.get(chat_id) or START
    state_handler = states_functions[int(user_state)]

    next_state = state_handler(update, context, moltin)
    redis_client.set(chat_id, next_state)


def handle_start_command(update, context, moltin):
    """Handle the START state."""

    query = update.callback_query
    if not query:
        with suppress(BadRequest):
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id-1
            )

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Press a button:",
        reply_markup=create_keyboard_markup(moltin)
    )
    return HANDLE_MENU


def create_keyboard_markup(moltin):
    """Create an InlineKeyboardMarkup with a list of all shop products."""

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in moltin.get_all_products()['data']
        if product['type'] == 'product'
    ]
    keyboard.append([get_cart_button()])
    return InlineKeyboardMarkup(keyboard)


def get_cart_button():
    """Make button to go to cart."""
    return InlineKeyboardButton('Shopping Cart', callback_data='cart')


def handle_main_menu(update, context, moltin):
    """Handle the HANDLE_MENU state."""

    query = update.callback_query
    if not query:
        return handle_start_command(update, context, moltin)

    query.answer()
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=query.message.message_id
    )

    if query.data == 'cart':
        return handle_cart_button(update, context, moltin)

    return handle_description_button(update, context, moltin)


def handle_cart_button(update, context, moltin):
    """Show cart to customer."""

    text = ''
    keyboard = []
    for item in moltin.get_cart_items(update.effective_chat.id)['data']:
        item_price = f"Price: {format_price(item['unit_price']['amount'])} per pound"
        item_quantity = f"{item['quantity']} pounds in cart for {format_price(item['value']['amount'])}"
        text += f"*{item['name']}*\n{item['description']}\n{item_price}\n{item_quantity}\n\n"
        keyboard.append([InlineKeyboardButton(f"Delete {item['name']} from cart", callback_data=item['id'])])

    if text:
        total_sum = moltin.get_cart(update.effective_chat.id)['data']['meta']['display_price']['with_tax']['amount']
        text += f'*Total: {format_price(total_sum)}*'
        keyboard.append(
            [
                InlineKeyboardButton('Payment', callback_data='payment'),
                get_back_button()
            ]
        )
    else:
        text = 'Cart is empty.'
        keyboard.append([get_back_button()])

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return HANDLE_CART


def format_price(price):
    return f'${price / 100}'


def get_back_button():
    """Make button to back to products list."""
    return InlineKeyboardButton('«‎ Back to Products List', callback_data='back')


def handle_cart_menu(update, context, moltin):
    """Handle the HANDLE_CART state."""

    query = update.callback_query
    if not query:
        return handle_start_command(update, context, moltin)

    query.answer()
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=query.message.message_id
    )
    if query.data == 'back':
        return handle_start_command(update, context, moltin)

    if query.data == 'payment':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Please send us your email:'
        )
        return WAITING_EMAIL

    moltin.delete_item_from_cart(update.effective_chat.id, query.data)
    return handle_cart_button(update, context, moltin)


def handle_email_message(update, context, moltin):
    """Handle the WAITING_EMAIL state."""

    pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
    match = re.match(pattern, update.message.text)
    if not match:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Email spelling error.\nPlease send us your email:'
        )
        return WAITING_EMAIL

    email = match.groups()[0]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Thanks! We've received your email: {email}.\nThe sales team will write to you soon."
    )
    return START


def handle_description_button(update, context, moltin):
    """Show product description to customer."""

    query = update.callback_query
    product_id = query.data
    product_details = moltin.get_product_by_id(product_id)['data']
    product_name = product_details['name']
    product_description = product_details['description']
    product_price = f"Price: {format_price(product_details['price'][0]['amount'])} per pound"

    image_id = product_details['relationships']['main_image']['data']['id']
    image = moltin.get_image_by_id(image_id)

    keyboard = [
        [
            InlineKeyboardButton('1 pound', callback_data=f'{product_id} 1'),
            InlineKeyboardButton('5 pounds', callback_data=f'{product_id} 5'),
            InlineKeyboardButton('10 pounds', callback_data=f'{product_id} 10')
        ],
        [
            get_cart_button(),
            get_back_button()
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=image,
        caption=f'\n\n*{product_name}*\n\n{product_description}\n\n{product_price}',
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return HANDLE_DESCRIPTION


def handle_description_menu(update, context, moltin):
    """Handle the HANDLE_DESCRIPTION state."""

    query = update.callback_query
    if not query:
        return handle_start_command(update, context, moltin)

    if query.data not in ['back', 'cart']:
        product_id, product_quantity = query.data.split()
        moltin.add_item_to_cart(update.effective_chat.id, product_id, int(product_quantity))
        query.answer('Product added to cart.')
        return HANDLE_DESCRIPTION

    query.answer()
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=query.message.message_id
    )

    if query.data == 'back':
        return handle_start_command(update, context, moltin)

    return handle_cart_button(update, context, moltin)


def handle_error(update, error):
    """Handle errors."""

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
