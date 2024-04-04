from odoo import models, fields, api

import requests
import logging

_logger = logging.getLogger(__name__)

class Product(models.Model):
    _name = 'holded_sync_odoo.odoo_products'
    _description = ''

    @api.model
    def insert_products(self):
        url = "https://api.holded.com/api/invoicing/v1/products"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        odoo_products = self.env['product.product'].search([])

        for odoo_product in odoo_products:
            # _logger.info(dir(odoo_product))
            # _logger.info(odoo_product.name)

            product_data = {
                "sku": odoo_product.code,
                "kind": "simple",
                "name": odoo_product.name,
                "desc": odoo_product.description,
                "price": odoo_product.lst_price,
            }

            _logger.info("Sending product data to Holded: %s", product_data)
            response = requests.post(url, headers=headers, json=product_data)
            _logger.info("Received response from Holded: %s", response.text)

    def sync_odoo_products_button(self):
        self.insert_products()
