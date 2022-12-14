# coding=utf-8

"""Maintain a class to work with Moltin API."""

import json
import time

import requests


class Moltin:
    """Wrap Moltin API."""

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_expiration = 0
        self._token = ''

    def get_access_token(self):
        """Provide an API access key."""

        if self.token_expiration - int(time.time()) >= 120:
            return self._token

        url = 'https://api.moltin.com/oauth/access_token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
        }
        response = requests.post(url, data=data)
        response.raise_for_status()

        token_details = response.json()
        self.token_expiration = token_details['expires']
        self._token = token_details['access_token']
        return self._token

    def get_headers(self):
        return {'Authorization': f'Bearer {self.get_access_token()}'}

    def create_products_from_json(self, json_file_path):
        """Create shop products from json file."""

        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            products_details = json.loads(json_file.read())

        for product_details in products_details:
            self.create_product(product_details)

    def create_product(self, product_details):
        """Create a product in the shop."""

        url = 'https://api.moltin.com/v2/products'
        headers = self.get_headers()
        headers['Content-Type'] = 'application/json'
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
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def load_images_from_json(self, json_file_path):
        """Load product images."""

        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            products_details = json.loads(json_file.read())

        for product in self.get_all_products()['data']:
            if product['type'] == 'product':
                for product_details in products_details:
                    if product['name'] == product_details['name']:
                        image_details = self.create_image(product_details['image_url'])
                        self.link_image_to_product(product['id'], image_details['data']['id'])
                        break

    def create_image(self, image_url):
        """Create image in Moltin database."""

        url = 'https://api.moltin.com/v2/files'
        files = {'file_location': (None, image_url)}
        response = requests.post(url, headers=self.get_headers(), files=files)
        response.raise_for_status()
        return response.json()

    def get_image_by_id(self, image_id):
        """Get image from Moltin API."""

        url = f'https://api.moltin.com/v2/files/{image_id}'
        headers = {'Authorization': f'Bearer {self.get_access_token()}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']['link']['href']

    def link_image_to_product(self, product_id, image_id):
        """Create link between product and image."""

        url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
        json_data = {
            'data': {
                'type': 'main_image',
                'id': image_id,
            },
        }
        response = requests.post(url, headers=self.get_headers(), json=json_data)
        response.raise_for_status()
        return response.json()

    def get_all_products(self):
        """Get a list of all shop products."""

        url = 'https://api.moltin.com/v2/products'
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    def get_product_by_id(self, product_id):
        """Get a product by its id."""

        url = f'https://api.moltin.com/v2/products/{product_id}'
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    def add_item_to_cart(self, customer_id, product_id, quantity):
        """Put item to customer's cart in specified quantity."""

        url = f'https://api.moltin.com/v2/carts/{customer_id}/items'
        headers = self.get_headers()
        headers['X-MOLTIN-CURRENCY'] = 'USD'
        json_data = {
            'data': {
                'id': product_id,
                'type': 'cart_item',
                'quantity': quantity
            }
        }
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def delete_item_from_cart(self, customer_id, product_id):
        """Exclude item from customer's cart."""

        url = f'https://api.moltin.com/v2/carts/{customer_id}/items/{product_id}'
        response = requests.delete(url, headers=self.get_headers())
        response.raise_for_status()

    def get_cart(self, customer_id):
        """Get customer's cart."""

        url = f'https://api.moltin.com/v2/carts/{customer_id}'
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    def get_cart_items(self, customer_id):
        """Get list of items in customer's cart."""

        url = f'https://api.moltin.com/v2/carts/{customer_id}/items'
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    def get_or_create_customer(self, customer_id, customer_email):
        """Write customer's data to Moltin database."""

        url = 'https://api.moltin.com/v2/customers'
        headers = self.get_headers()
        headers['Content-Type'] = 'application/json' 
        params = {'filter': f'eq(email,{customer_email})'}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        customer_info = response.json()
        if customer_info['data']:
            return customer_info, False

        json_data = {
            'data': {
                'type': 'customer',
                'name': str(customer_id),
                'email': customer_email
            }
        }
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json(), True
