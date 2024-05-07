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
    processed_payment = fields.Char(string="Processed", default="Not Processed")

    def sync_payments_button(self):
        try:
            self.bring_payments_odoo()
            processed_payments = self.env['holded_sync_odoo.odoo_payments'].search(
                [('processed_payment', '=', 'Processed')])
            _logger.info("Number of payments processed: %s", len(processed_payments))

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

                existing_payments = self.env['holded_sync_odoo.odoo_payments'].search([])

                for payment_data in payments_list:
                    timestamp = payment_data.get("date")

                    if timestamp:
                        payment_date = datetime.utcfromtimestamp(timestamp)

                        payment_info = {
                            "holded_id": payment_data.get('id'),
                            "contact_id": payment_data.get('contactId'),
                            "contact_name": payment_data.get('contactName'),
                            "amount": payment_data.get("amount"),
                            "desc": payment_data.get("desc"),
                            "date": payment_date.date(),
                        }

                        payment_exist = existing_payments.filtered(
                            lambda pa: pa.desc == payment_info.get('desc'))
                        if payment_exist:
                            payment_exist.write(payment_info)
                        else:
                            new_payment = self.env['holded_sync_odoo.odoo_payments'].create(payment_info)
                            new_payment.write({'processed_payment': "Processed"})
                            _logger.info("New payment created and processed: %s", new_payment)

        except Exception as e:
            _logger.error("An error occurred while bringing payments from Holded to Odoo: %s", e)
