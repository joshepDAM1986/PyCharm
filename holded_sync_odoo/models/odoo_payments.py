from odoo import models, fields
from datetime import datetime
import logging
import requests
import pytz

_logger = logging.getLogger(__name__)


class Payment(models.Model):
    _name = 'holded_sync_odoo.odoo_payments'
    _description = 'Odoo payments to be synchronized and exported to Holded ERP'

    holded_payment_id = fields.Char(string="Holded Payment ID")
    bankId = fields.Char(string="Bank ID")
    contactId = fields.Char(string="Contact ID")
    contactName = fields.Char(string='Contact Name')
    amount = fields.Float(string='Amount')
    date = fields.Date(string="Date")
    desc = fields.Char(string='Description')
    documentType = fields.Char(string='Document Type')
    documentId = fields.Char(string='Document ID')
    last_sync = fields.Datetime(string='Last Sync', readonly=True, default=False)
    invoiceNum = fields.Char(string='Document Number')
    odoo_document_id = fields.Char(string='Odoo Document ID')
    odoo_payment_id = fields.Char(string="Odoo Payment ID")
    odoo_document_name = fields.Char(string='Odoo Document Name')
    odoo_payment_name = fields.Char(string="Odoo Payment Name")

    @property
    def holded_api_url(self):
        return "https://api.holded.com/api/invoicing/v1/payments"

    @property
    def holded_api_headers(self):
        config = self.env['holded.sync.odoo.apikeyconfig'].search([], limit=1)
        api_key = config.api_key if config else ''
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "key": api_key
        }

    def bring_payments(self):
        try:
            existing_payments = self.env['holded_sync_odoo.odoo_payments'].search([])
            existing_payments.unlink()

            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)

            if response.status_code == 200:
                payment_list = response.json()
                _logger.info("Received payment list: %s", payment_list)

                timezone = pytz.timezone('Europe/Madrid')

                for payment_data in payment_list:
                    holded_payment_id = payment_data.get('id')
                    desc = payment_data.get('desc')

                    odoo_payment_id = desc.split(' ')[0]
                    odoo_payment_id_stripped = odoo_payment_id.strip()

                    odoo_document_id = desc.split(' ')[1]
                    odoo_document_id_stripped = odoo_document_id.strip()

                    odoo_document_name = self.env['account.move'].search([('id', '=', odoo_document_id_stripped)],
                                                                         limit=1).name
                    odoo_payment_name = self.env['account.payment'].search([('id', '=', odoo_payment_id_stripped)],
                                                                           limit=1).name

                    date_timestamp = payment_data.get('date')
                    utc_datetime = datetime.fromtimestamp(date_timestamp, pytz.utc)
                    my_datetime = utc_datetime.astimezone(timezone)
                    date = my_datetime.strftime('%Y-%m-%d')

                    payment_info = {
                        'odoo_document_id': odoo_document_id_stripped,
                        'odoo_payment_id': odoo_payment_id_stripped,
                        'odoo_document_name': odoo_document_name,
                        'odoo_payment_name': odoo_payment_name,
                        'holded_payment_id': holded_payment_id,
                        'bankId': payment_data.get('bankId') or 'Cash',
                        'contactId': payment_data.get('contactId'),
                        'contactName': payment_data.get('contactName'),
                        'amount': payment_data.get('amount'),
                        'date': date,
                        'documentType': payment_data.get('documentType'),
                        'documentId': payment_data.get('documentId'),
                    }

                    self.env['holded_sync_odoo.odoo_payments'].create(payment_info)

                self.sudo().search([], limit=1).write({'last_sync': fields.Datetime.now()})

        except Exception as e:
            _logger.error("An error occurred while bringing payments from Holded to Odoo: %s", e)

    def sync_payments_button(self):
        try:
            self.bring_payments()
        except Exception as e:
            _logger.error("An error occurred while syncing invoices: %s", e)
