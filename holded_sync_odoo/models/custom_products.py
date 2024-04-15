from odoo import models, fields

import requests


class Product(models.Model):
    _name = 'holded_sync_odoo.custom_products'
    _description = 'Custom Odoo module products to be synchronized with Holded'

    holded_id = fields.Char(string='Holded ID')
    sku = fields.Char(string='SKU')
    kind = fields.Char(string='Kind')
    name = fields.Char(string='Name')
    price = fields.Float(string='Price')
    purchasePrice = fields.Float(string='Purchase Price')
    barcode = fields.Char(string='Barcode')
    total = fields.Float(string='Total')

    def insert_products(self):
        url = "https://api.holded.com/api/invoicing/v1/products"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        odoo_products = self.env['holded_sync_odoo.custom_products'].search([])

        for odoo_product in odoo_products:

            product_data = {
                "sku": odoo_product.code,
                "kind": "simple",
                "name": odoo_product.name,
                "price": odoo_product.lst_price,
                "purchasePrice": odoo_product.standard_price,
                "total": odoo_product.list_price,
                "barcode": odoo_product.barcode,
            }

            requests.post(url, headers=headers, json=product_data)

    def bring_products(self):
        url = "https://api.holded.com/api/invoicing/v1/products"
        headers = {
            "accept": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        response = requests.get(url, headers=headers)
        product_list = response.json()

        odoo_products = self.env['holded_sync_odoo.custom_products'].search([])

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

            product_exist = odoo_products.filtered(lambda p: p.sku == product_data.get('sku'))
            if not product_exist:
                self.env['holded_sync_odoo.custom_products'].create(product_info)
            else:
                product_exist.write(product_info)

    def sync_products_button(self):
        self.bring_products()

    # def _cron_sync_holded_product(self):
    #     self.insert_products()
    #     self.bring_products()
