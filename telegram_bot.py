# coding=utf-8

"""Организует работу telegram-бота магазина рыбы."""

import os

from dotenv import load_dotenv

from moltin import Moltin


def main():
    load_dotenv()

    moltin = Moltin(os.environ['MOLTIN_CLIENT_ID'], os.environ['MOLTIN_CLIENT_SECRET'])
    shop_products = moltin.get_all_products()
    print(shop_products)


if __name__ == '__main__':
    main()
