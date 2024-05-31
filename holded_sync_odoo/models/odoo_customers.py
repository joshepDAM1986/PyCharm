from odoo import models, fields
import requests
import logging

_logger = logging.getLogger(__name__)


class Customer(models.Model):
    _name = 'holded_sync_odoo.odoo_customers'
    _description = 'Odoo customers to be synchronized and exported to Holded ERP'

    holded_customer_id = fields.Char(string='Holded Customer ID')
    name = fields.Char(string='Name')
    code = fields.Char(string='Customer Code')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    phone = fields.Integer(string='Phone')
    mobile = fields.Integer(string='Mobile')
    address = fields.Char(string='Address')
    city = fields.Char(string='City')
    postalCode = fields.Char(string='Postal Code')
    province = fields.Char(string='Province')
    country = fields.Char(string='Country')
    countryCode = fields.Char(string='Country Code')
    tags = fields.Char(string='Tags')

    @property
    def holded_api_url(self):
        return "https://api.holded.com/api/invoicing/v1/contacts"

    @property
    def holded_api_headers(self):
        config = self.env['holded.sync.odoo.apikeyconfig'].search([], limit=1)
        api_key = config.api_key if config else ''
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "key": api_key
        }

    def insert_or_update_customer(self, odoo_customer, holded_contacts):
        try:
            is_company = odoo_customer.is_company
            contact_type = 0 if is_company else 1
            tags = odoo_customer.category_id.mapped('name')

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

            if odoo_customer._name == 'res.partner':
                if odoo_customer.bank_ids:
                    for bank in odoo_customer.bank_ids:
                        customer_data.update({
                            "swift": bank.bank_id.bic or '',
                            "iban": bank.acc_number or '',
                        })

            holded_contact = next((contact for contact in holded_contacts if contact['code'] == odoo_customer.vat),
                                  None)

            if holded_contact:
                url = f"{self.holded_api_url}/{holded_contact['id']}"
                response = requests.put(url, headers=self.holded_api_headers, json=customer_data)
                if response.status_code == 200:
                    _logger.info("Updated customer in Holded: %s", customer_data)
                else:
                    _logger.error("Error while updating customer in Holded: %s", response.text)
            else:
                response = requests.post(self.holded_api_url, headers=self.holded_api_headers, json=customer_data)
                if response.status_code == 201:
                    _logger.info("Created customer in Holded: %s", customer_data)
                else:
                    _logger.error("Error while creating customer in Holded: %s", response.text)
        except Exception as e:
            _logger.error("An error occurred while inserting or updating customer in Holded: %s", e)

    def insert_customers(self):
        try:
            self.bring_customers()
            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)
            holded_contacts = response.json()

            odoo_customers = self.env['res.partner'].search([])
            for odoo_customer in odoo_customers:
                self.insert_or_update_customer(odoo_customer, holded_contacts)
        except Exception as e:
            _logger.error("An error occurred while inserting customers in Holded: %s", e)

    def bring_customers(self):
        try:
            existing_customers = self.env['holded_sync_odoo.odoo_customers'].search([])
            existing_customers.unlink()

            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)

            if response.status_code == 200:
                customers_list = response.json()

                for customer_data in customers_list:
                    customer_info = {
                        "holded_customer_id": customer_data.get('id'),
                        "name": customer_data.get('name'),
                        "code": customer_data.get('code'),
                        "email": customer_data.get('email'),
                        "website": customer_data.get('socialNetworks', {}).get('website'),
                        "mobile": customer_data.get('mobile'),
                        "phone": customer_data.get('phone'),
                        "address": customer_data.get('billAddress', {}).get('address'),
                        "city": customer_data.get('billAddress', {}).get('city'),
                        "postalCode": customer_data.get('billAddress', {}).get('postalCode'),
                        "province": customer_data.get('billAddress', {}).get('province'),
                        "country": customer_data.get('billAddress', {}).get('country'),
                        "countryCode": customer_data.get('billAddress', {}).get('countryCode'),
                        "tags": ','.join(customer_data.get('tags', [])),
                    }

                    self.env['holded_sync_odoo.odoo_customers'].create(customer_info)

        except Exception as e:
            _logger.error("An error occurred while bringing customers from Holded to Odoo: %s", e)

    def sync_customers_button(self):
        try:
            self.bring_customers()
        except Exception as e:
            _logger.error("An error occurred while syncing customers: %s", e)
