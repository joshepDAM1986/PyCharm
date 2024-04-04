from odoo import models, fields, api

import requests

class Product(models.Model):
    _name = 'holded_sync_odoo.custom_products'
    _description = ''

    holded_id = fields.Char(string='Holded ID', unique=True)
    sku = fields.Char(string='SKU', unique=True)
    kind = fields.Char(string='Kind')
    name = fields.Char(string='Name')
    desc = fields.Text(string='Description')
    price = fields.Float(string='Price')
    total = fields.Float(string='Total')

    @api.model
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
                "id": odoo_product.id,
                "sku": odoo_product.sku,
                "kind": odoo_product.kind,
                "name": odoo_product.name,
                "desc": odoo_product.desc,
                "price": odoo_product.price,
                "total": odoo_product.total
            }
            
            requests.post(url, headers=headers, json=product_data)


    @api.model
    def bring_products(self):
        url = "https://api.holded.com/api/invoicing/v1/products"
        headers = {
            "accept": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        response = requests.get(url, headers=headers)
        product_list = response.json()

        #comprueba todos los productos de odoo
        odoo_products = self.env['holded_sync_odoo.custom_products'].search([])

        for product_data in product_list:

            product_info = {
                'holded_id': product_data.get('id'),
                'sku': product_data.get('sku'),
                'kind':product_data.get('kind'),
                'name': product_data.get('name'),
                'desc': product_data.get('desc'),
                'price': product_data.get('price'),
                'total': product_data.get('total')
            }

            #comprueba que los productos de holded existen en odoo buscando su id de holded
            #si no existen los crea y si existen los actualiza.

            product_exist = odoo_products.filtered(lambda p: p.sku == product_data.get('sku'))
            if not product_exist:
                self.env['holded_sync_odoo.custom_products'].create(product_info)
            else:
                product_exist.write(product_info)

        #inserta en una lista todos los sku de los productos
        holded_products_sku = [product_data.get('sku') for product_data in product_list]

        #si ya no existen productos antes existentes en holded los borra de odoo
        products_to_delete = odoo_products.filtered(lambda p: p.sku not in holded_products_sku)
        products_to_delete.unlink()

    def sync_custom_products_button(self):
        self.insert_products()


    # #ejecuta las funciones periódicamente en intervalos configurados en la view
    # @api.model
    # def _cron_sync_holded_product(self):
    #     self.insert_products()
    #     self.bring_products()