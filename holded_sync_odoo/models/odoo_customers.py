from odoo import models, fields

import requests
import logging

_logger = logging.getLogger(__name__)


class Customer(models.Model):
    _name = 'holded_sync_odoo.odoo_customers'
    _description = 'Odoo internal customers to be synchronized and exported to Holded ERP'

    holded_id = fields.Char(string='Holded ID')
    name = fields.Char(string='Name')
    code = fields.Char(string='Customer Code')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    phone = fields.Integer(string='Phone')
    mobile = fields.Integer(string='Mobile')
    address = fields.Char(string='Address')

    def insert_or_update_customer(self, odoo_customer, holded_contacts):
        is_company = odoo_customer.is_company
        contact_type = 0 if is_company else 1
        tags = odoo_customer.category_id.mapped('name')

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        customer_data = {
            "isperson": contact_type,
            "name": odoo_customer.name,
            "code": odoo_customer.vat,
            "email": odoo_customer.email or '',
            "mobile": odoo_customer.mobile or '',
            "phone": odoo_customer.phone or '',
            "billAddress": {
                "address": odoo_customer.street or '',
                "city": odoo_customer.city or '',
                "postalCode": odoo_customer.zip or '',
                "province": odoo_customer.state_id.name or '',
                "country": odoo_customer.country_id.name or '',
                "countryCode": odoo_customer.country_id.code or '',
            },
            "socialNetworks": {
                "website": odoo_customer.website or '',
            },
            "tags": tags
        }

        holded_contact = next((contact for contact in holded_contacts if contact['code'] == odoo_customer.vat), None)

        if holded_contact:
            url_update_holded_contact = f"https://api.holded.com/api/invoicing/v1/contacts/{holded_contact['id']}"
            response = requests.put(url_update_holded_contact, headers=headers, json=customer_data)
            if response.status_code == 200:
                _logger.info("Updated customer in Holded: %s", customer_data)
            else:
                _logger.error("Error while updating customer in Holded: %s", response.text)
        else:
            url_create_holded_contact = "https://api.holded.com/api/invoicing/v1/contacts"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }
            response = requests.post(url_create_holded_contact, headers=headers, json=customer_data)
            if response.status_code == 200:
                holded_customer_id = response.json().get('id')
                odoo_customer.write({'holded_id': holded_customer_id})
                _logger.info("Created customer in Holded: %s", customer_data)
            else:
                _logger.error("Error while creating customer in Holded: %s", response.text)

    def insert_customers(self):
        url_get_holded_contacts = "https://api.holded.com/api/invoicing/v1/contacts"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        response = requests.get(url_get_holded_contacts, headers=headers)
        holded_contacts = response.json()

        odoo_customers = self.env['res.partner'].search([])

        for odoo_customer in odoo_customers:
            self.insert_or_update_customer(odoo_customer, holded_contacts)

    def bring_customers(self):
        url = "https://api.holded.com/api/invoicing/v1/contacts"
        headers = {
            "accept": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            customers_list = response.json()
            odoo_customers = self.env['holded_sync_odoo.odoo_customers'].search([])

            for customer_data in customers_list:
                customer_info = {
                    "holded_id": customer_data.get('id'),
                    "name": customer_data.get('name'),
                    "code": customer_data.get('code'),
                    "email": customer_data.get('email'),
                    "website": customer_data.get('website'),
                    "mobile": customer_data.get('mobile'),
                    "phone": customer_data.get('phone'),
                    "address": customer_data.get('address'),
                }

                customer_exist = odoo_customers.filtered(lambda c: c.code == customer_info.get('code'))
                if not customer_exist:
                    self.env['holded_sync_odoo.odoo_customers'].create(customer_info)
                else:
                    customer_exist.write(customer_info)
        else:
            _logger.error("Error while fetching customers from Holded: %s", response.text)

    def sync_odoo_customers_button(self):
        self.insert_customers()
        self.bring_customers()
