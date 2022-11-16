# coding=utf-8

"""Организует работу telegram-бота магазина рыбы."""

import os

from dotenv import load_dotenv

from moltin import Moltin


def main():
    load_dotenv()

    moltin = Moltin(os.environ['MOLTIN_CLIENT_ID'], os.environ['MOLTIN_CLIENT_SECRET'])
    products = moltin.get_all_products()
    user_id = os.environ['TELEGRAM_MODERATOR_CHAT_ID']
    print(moltin.get_cart_items(user_id))


if __name__ == '__main__':
    main()
