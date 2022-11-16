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
    print(moltin.add_product_to_cart(user_id, product_id=products['data'][0]['id'], quantity=1))


if __name__ == '__main__':
    main()
