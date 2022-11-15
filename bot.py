# coding=utf-8

"""Получает список продуктов магазина с сервиса Moltin."""

import json
import logging
import os

import requests
from dotenv import load_dotenv


logger = logging.getLogger('fish_shop_bot.logger')


def main():
    load_dotenv()

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)

    data = {
        'client_id': os.environ['MOLTIN_CLIENT_ID'],
        'client_secret': os.environ['MOLTIN_CLIENT_SECRET'],
        'grant_type': 'client_credentials',
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()

    access_token = response.json()['access_token']
    print(access_token)

    headers = {'Authorization': f'Bearer {access_token}',}
    response = requests.get('https://api.moltin.com/pcm/products', headers=headers)
    response.raise_for_status()

    shop_products = response.json()
    print(shop_products)


if __name__ == '__main__':
    main()
