from odoo import models, fields, api

import requests
import logging

_logger = logging.getLogger(__name__)


class Customer(models.Model):
    _name = 'holded_sync_odoo.odoo_customers'
    _description = ''

    @api.model
    def insert_customers(self):
        url = "https://api.holded.com/api/invoicing/v1/contacts"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        odoo_customers = self.env['res.partner'].search([])

        for odoo_customer in odoo_customers:

            # _logger.info(dir(odoo_customer))
            # _logger.info(odoo_customer.contact_address)

            customer_data = {
                "name": odoo_customer.name,
                "code": odoo_customer.ref,
                "email": odoo_customer.email or '',
                "mobile": odoo_customer.mobile or '',
                "phone": odoo_customer.phone or '',
                "tradeName":odoo_customer.commercial_company_name or '',
                "billAddress": {
                    "address": odoo_customer.contact_address or '',
                    "city": odoo_customer.city or '',
                    "postalCode": odoo_customer.zip or '',
                    "province": odoo_customer.state_id.name or '',
                    "country": odoo_customer.country_id.name or '',
                    "countryCode": odoo_customer.country_id.code or '',
                },
                "socialNetworks": {
                    "website": odoo_customer.website or '',
                    }
            }

            _logger.info("Sending customer data to Holded: %s", customer_data)
            response = requests.post(url, headers=headers, json=customer_data)
            _logger.info("Received response from Holded: %s", response.text)

    def sync_odoo_customers_button(self):
        self.insert_customers()