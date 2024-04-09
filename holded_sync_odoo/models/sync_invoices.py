from odoo import models, fields

import requests
import logging

from datetime import datetime

_logger = logging.getLogger(__name__)


class SyncInvoices(models.Model):
    _name = 'holded_sync_odoo.sync_invoices'
    _description = 'Odoo internal invoices to be synchronized and exported to Holded ERP'

    def insert_invoices(self):

        odoo_invoices = self.env['account.move'].search([])

        if not odoo_invoices:
            _logger.warning("There is not any invoice in odoo.")
            return

        url = "https://api.holded.com/api/invoicing/v1/documents/invoice"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        for odoo_invoice in odoo_invoices:
            if not odoo_invoice.invoice_date:
                _logger.warning("The invoice %s doesn't have a defined date.", odoo_invoice.id)
                continue

            if not odoo_invoice.invoice_date_due:
                _logger.warning("The invoice %s doesn't have a defined due date.", odoo_invoice.id)
                continue

            contact_code = odoo_invoice.partner_id.vat

            invoice_products = []
            for line in odoo_invoice.invoice_line_ids:
                invoice_products.append({
                    "units": line.quantity,
                    "sku": line.product_id.default_code
                })

            invoice_datetime = datetime.combine(odoo_invoice.invoice_date, datetime.min.time())
            invoice_dateduetime = datetime.combine(odoo_invoice.invoice_date_due, datetime.min.time())

            timestamp_date = int(invoice_datetime.timestamp())
            timestamp_datedue = int(invoice_dateduetime.timestamp())

            payload = {
                "contactCode": contact_code,
                "date": timestamp_date,
                "dueDate": timestamp_datedue,
                "items": invoice_products,
            }

            _logger.info("Payload sent to Holded for invoice %s: %s", odoo_invoice.id, payload)
            response = requests.post(url, json=payload, headers=headers)
            _logger.info("holded request for invoice %s: %s", odoo_invoice.id, response.text)

    def sync_invoices_to_holded(self):
        self.insert_invoices()