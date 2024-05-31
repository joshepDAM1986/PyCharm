
from odoo import models, fields
import requests
import logging

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _name = 'holded_sync_odoo.odoo_products'
    _description = 'Odoo products to be synchronized and exported to Holded ERP'

    holded_product_id = fields.Char(string='Holded Product ID')
    sku = fields.Char(string='SKU')
    kind = fields.Char(string='Kind')
    name = fields.Char(string='Name')
    price = fields.Float(string='Price')
    purchasePrice = fields.Float(string='Purchase Price')
    cost = fields.Float(string='Cost Price')
    barcode = fields.Char(string='Barcode')

    @property
    def holded_api_url(self):
        return "https://api.holded.com/api/invoicing/v1/products"

    @property
    def holded_api_headers(self):
        config = self.env['holded.sync.odoo.apikeyconfig'].search([], limit=1)
        api_key = config.api_key if config else ''
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "key": api_key
        }

    def insert_or_update_products(self, odoo_product, holded_products):
        try:
            product_data = {
                "sku": odoo_product.code,
                "kind": "simple",
                "name": odoo_product.name,
                "price": odoo_product.list_price,
                "purchasePrice": odoo_product.standard_price,
                "cost": odoo_product.standard_price,
                "barcode": odoo_product.barcode,
                "tax": odoo_product.taxes_id.amount
            }

            holded_product = next((product for product in holded_products if product['sku'] ==
                                   odoo_product.default_code), None)

            if holded_product:
                url = f"{self.holded_api_url}/{holded_product['id']}"
                response = requests.put(url, headers=self.holded_api_headers, json=product_data)
                if response.status_code == 200:
                    _logger.info("Updated product in Holded: %s", product_data)
                else:
                    _logger.error("Error while updating product in Holded: %s", response.text)
            else:
                response = requests.post(self.holded_api_url, headers=self.holded_api_headers, json=product_data)
                if response.status_code == 201:
                    _logger.info("Created product in Holded: %s", product_data)
                else:
                    _logger.error("Error while creating product in Holded: %s", response.text)
        except Exception as e:
            _logger.error("An error occurred while inserting or updating product in Holded: %s", e)

    def insert_products(self):
        try:

            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)
            holded_products = response.json()

            odoo_products = self.env['product.product'].search([])

            for odoo_product in odoo_products:
                self.insert_or_update_products(odoo_product, holded_products)
        except Exception as e:
            _logger.error("An error occurred while inserting products in Holded: %s", e)

    def bring_products(self):
        try:
            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)
            if response.status_code == 200:
                product_list = response.json()
                odoo_products = self.env['holded_sync_odoo.odoo_products'].search([])

                for product_data in product_list:
                    product_info = {
                        "holded_product_id": product_data.get('id'),
                        "sku": product_data.get('sku'),
                        "kind": "simple",
                        "name": product_data.get('name'),
                        "price": product_data.get('price'),
                        "purchasePrice": product_data.get('purchasePrice'),
                        "barcode": product_data.get('barcode'),
                    }

                    product_exist = odoo_products.filtered(lambda p: p.sku == product_info.get('sku'))
                    if not product_exist:
                        self.env['holded_sync_odoo.odoo_products'].create(product_info)
                    else:
                        product_exist.write(product_info)
            else:
                _logger.error("Error while fetching products from Holded: %s", response.text)
        except Exception as e:
            _logger.error("An error occurred while bringing products from Holded to Odoo: %s", e)

    def sync_products_button(self):
        try:
            self.bring_products()
        except Exception as e:
            _logger.error("An error occurred while syncing products: %s", e)
