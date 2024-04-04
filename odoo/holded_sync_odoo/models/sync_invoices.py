from odoo import models, fields, api

import requests
import logging

_logger = logging.getLogger(__name__)

class Product(models.Model):
    _name = 'holded_sync_odoo.sync_invoices'
    _description = ''

    @api.model
    def insert_invoices(self):
        url = "https://api.holded.com/api/invoicing/v1/documents/invoice"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        odoo_invoices = self.env['account.move'].search([])
        odoo_products = self.env['product.product'].search([])

        for odoo_invoice in odoo_invoices:
            # _logger.info(dir(odoo_invoice))
            # _logger.info (odoo_invoice)


            # Asegúrate de obtener el nombre del contacto correcto
            contact_name = odoo_invoice.partner_id.name if odoo_invoice.partner_id else ''
            contact_nif = odoo_invoice.partner_id.vat if odoo_invoice.partner_id else ''
            date = odoo_invoice.invoice_date.strftime('%Y-%m-%d') if odoo_invoice.invoice_date else ''


            product_lines = []
            for odoo_product in odoo_products:
                # _logger.info(dir(odoo_product))
                # _logger.info(odoo_product.tax_string)

                product_info = {
                    "kind": "simple",
                    "name": odoo_product.name,
                    "desc": odoo_product.description,
                    "price": odoo_product.price,
                }
                product_lines.append(product_info)

            invoice_data = {
                "name": odoo_invoice.name,
                "contact": contact_name,
                "code": contact_nif,
                "date": date,
                "products": product_lines,
            }

            _logger.info("Sending invoice data to Holded: %s", invoice_data)
            response = requests.post(url, headers=headers, json=invoice_data)
            _logger.info("Received invoice from Holded: %s", response.text)

    def sync_invoices_to_holded(self):
        self.insert_invoices()