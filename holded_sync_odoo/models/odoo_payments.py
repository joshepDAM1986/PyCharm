from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Payment(models.Model):
    _name = 'holded_sync_odoo.odoo_payments'
    _description = 'Odoo payments to be synchronized and exported to Holded ERP'

    holded_id = fields.Char(string='Payment ID')
    contact_id = fields.Char(string="Contact ID")
    contact_name = fields.Char(string='Contact Name')
    amount = fields.Float(string='Amount')
    desc = fields.Char(string='Description')
    date = fields.Date(string="Date")

    def sync_payments_button(self):
        try:
            self.bring_payments_odoo()
        except Exception as e:
            _logger.error("An error occurred while syncing payments: %s", e)

    def bring_payments_odoo(self):
        try:
            url = "https://api.holded.com/api/invoicing/v1/payments"
            headers = {
                "accept": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                payments_list = response.json()

                odoo_payments = self.env['holded_sync_odoo.odoo_payments']
                odoo_payments.search([]).unlink()

                for payment_data in payments_list:
                    timestamp = payment_data.get("date")

                    if timestamp:
                        payment_date = datetime.utcfromtimestamp(timestamp)

                        odoo_payment = {
                            "holded_id": payment_data.get('id'),
                            "contact_id": payment_data.get('contactId'),
                            "contact_name": payment_data.get('contactName'),
                            "amount": payment_data.get("amount"),
                            "desc": payment_data.get("desc"),
                            "date": payment_date.date()
                        }

                        self.env['holded_sync_odoo.odoo_payments'].create(odoo_payment)

        except Exception as e:
            _logger.error("An error occurred while bringing payments from Holded to Odoo: %s", e)

