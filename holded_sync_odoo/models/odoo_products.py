from odoo import models, fields

import requests
import logging

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _name = 'holded_sync_odoo.odoo_products'
    _description = 'Odoo internal products to be synchronized and exported to Holded ERP'

    holded_id = fields.Char(string='Holded ID')
    sku = fields.Char(string='SKU')
    kind = fields.Char(string='Kind')
    name = fields.Char(string='Name')
    price = fields.Float(string='Price')
    purchasePrice = fields.Float(string='Purchase Price')
    barcode = fields.Char(string='Barcode')
    total = fields.Float(string='Total')

    def insert_or_update_product(self, odoo_product, holded_products):
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        product_data = {
            "sku": odoo_product.code,
            "kind": "simple",
            "name": odoo_product.name,
            "price": odoo_product.lst_price,
            "purchasePrice": odoo_product.standard_price,
            "total": odoo_product.list_price,
            "barcode": odoo_product.barcode,

        }

        holded_product = next((product for product in holded_products if product['sku'] == odoo_product.default_code), None)

        if holded_product:
            url_update_holded_product = f"https://api.holded.com/api/invoicing/v1/products/{holded_product['id']}"

            response = requests.put(url_update_holded_product, headers=headers, json=product_data)
            if response.status_code == 200:
                _logger.info("Updated product in Holded: %s", product_data)
            else:
                _logger.error("Error while updating product in Holded: %s", response.text)
        else:
            url_create_holded_product = "https://api.holded.com/api/invoicing/v1/products"
            response = requests.post(url_create_holded_product, headers=headers, json=product_data)
            if response.status_code == 200:
                holded_product_id = response.json().get('id')
                odoo_product.write({'holded_id': holded_product_id})
                _logger.info("Created product in Holded: %s", product_data)
            else:
                _logger.error("Error while creating product in Holded: %s", response.text)

    def insert_products(self):
        url_get_holded_products = "https://api.holded.com/api/invoicing/v1/products"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        response = requests.get(url_get_holded_products, headers=headers)
        holded_products = response.json()

        odoo_products = self.env['product.product'].search([])

        for odoo_product in odoo_products:
            self.insert_or_update_product(odoo_product, holded_products)

    def bring_products(self):
        url = "https://api.holded.com/api/invoicing/v1/products"
        headers = {
            "accept": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            product_list = response.json()
            odoo_products = self.env['holded_sync_odoo.odoo_products'].search([])

            for product_data in product_list:
                product_info = {
                    "holded_id": product_data.get('id'),
                    "sku": product_data.get('sku'),
                    "kind": "simple",
                    "name": product_data.get('name'),
                    "price": product_data.get('price'),
                    "purchasePrice": product_data.get('purchasePrice'),
                    "total": product_data.get('total'),
                    "barcode": product_data.get('barcode'),
                }

                product_exist = odoo_products.filtered(lambda p: p.sku == product_info.get('sku'))
                if not product_exist:
                    self.env['holded_sync_odoo.odoo_products'].create(product_info)
                else:
                    product_exist.write(product_info)
        else:
            _logger.error("Error while fetching products from Holded: %s", response.text)

    def sync_odoo_products_button(self):
        self.insert_products()
        self.bring_products()
