# coding=utf-8

"""Содержит классы и функции для работы с сервисом Moltin."""

import json
import time

import requests


class Moltin:
    """Предоставляет доступ к API сервиса Moltin."""

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_expiration = 0
        self._token = ''

    def create_product(self, product_details):
        """Создаёт продукт в магазине."""

        json_data = {
            'data': {
                'type': 'product',
                'name': product_details['name'],
                'slug': f"product-item-{product_details['id']}",
                'sku': str(product_details['id']),
                'description': product_details['description'],
                'manage_stock': False,
                'price': [
                    {
                        'amount': product_details['price'],
                        'currency': 'USD',
                        'includes_tax': True,
                    },
                ],
                'status': 'live',
                'commodity_type': 'physical',
            },
        }
        headers = {
            'Authorization': f'Bearer {self.get_access_token()}',
            'Content-Type': 'application/json',
        }
        response = requests.post('https://api.moltin.com/v2/products', headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def create_products_from_json(self, json_file_path):
        """Создаёт продукты в магазине из json-файла."""

        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            products_details = json.loads(json_file.read())

        for product_details in products_details:
            self.create_product(product_details)

    def get_access_token(self):
        """Предоставляет ключ доступа к API сервиса Moltin."""

        if self.token_expiration - int(time.time()) >= 120:
            return self._token

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
        }
        response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
        response.raise_for_status()

        token_details = response.json()
        self.token_expiration = token_details['expires']
        self._token = token_details['access_token']
        return self._token

    def get_all_products(self):
        """Получает список всех продуктов магазина с сервиса Moltin."""

        headers = {'Authorization': f'Bearer {self.get_access_token()}'}
        response = requests.get('https://api.moltin.com/v2/products', headers=headers)
        response.raise_for_status()
        return response.json()
