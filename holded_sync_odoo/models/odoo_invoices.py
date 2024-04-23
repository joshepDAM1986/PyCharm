from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Invoice(models.Model):
    _name = 'holded_sync_odoo.odoo_invoices'
    _description = 'Odoo internal invoices to be synchronized and exported to Holded ERP'

    holded_id = fields.Char(string='Holded Invoice ID')
    invoiceNum = fields.Char(string='Invoice Number')
    contactName = fields.Char(string='Customer Name')
    holded_payment_state = fields.Char(string='Payment State')

    def insert_holded_invoices(self):
        try:
            odoo_invoices = self.env['account.move'].search([])
            batch_size = 100
            total_invoices = len(odoo_invoices)
            for index in range(0, total_invoices, batch_size):
                batch_invoices = odoo_invoices[index:index + batch_size]
                self.process_batch(batch_invoices)
        except Exception as e:
            _logger.error("An error occurred while inserting invoices into Holded: %s", e)

    def process_batch(self, batch_invoices):
        try:
            for odoo_invoice in batch_invoices:
                if (odoo_invoice.state != "draft"
                        and odoo_invoice.move_type != "entry"
                        and odoo_invoice.move_type == "out_invoice") :
                    url = "https://api.holded.com/api/invoicing/v1/documents/invoice"
                    headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "key": "cf6626233fa4b33a99aa841dd37a11a9"
                    }
                    contact_code = odoo_invoice.partner_id.vat
                    invoice_datetime = datetime.combine(odoo_invoice.invoice_date or fields.Date.today(),
                                                        datetime.min.time())
                    invoice_dateduetime = datetime.combine(odoo_invoice.invoice_date_due or fields.Date.today(),
                                                           datetime.min.time())
                    timestamp_date = int(invoice_datetime.timestamp())
                    timestamp_datedue = int(invoice_dateduetime.timestamp())
                    invoice_data = {
                        "invoiceNum": odoo_invoice.name,
                        "contactCode": contact_code,
                        "date": timestamp_date,
                        "dueDate": timestamp_datedue,
                        "items": [{
                            "units": line.quantity,
                            "sku": line.product_id.default_code
                        } for line in odoo_invoice.invoice_line_ids],
                    }
                    holded_invoice_exists = self.env['holded_sync_odoo.odoo_invoices'].search([
                        ('invoiceNum', '=', odoo_invoice.name)
                    ])
                    if not holded_invoice_exists:
                        response = requests.post(url, json=invoice_data, headers=headers)
                        if response.status_code == 200:
                            _logger.info("Invoice %s successfully inserted: %s", odoo_invoice.id, response.text)
                        else:
                            _logger.error("Error inserting invoice %s in Holded: %s", odoo_invoice.id, response.text)
                    else:
                        _logger.info("Invoice %s already exists in Holded, skipping insertion", odoo_invoice.name)
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def pay_holded_invoices(self):
        try:
            odoo_paid_invoices = self.env['account.move'].search([('payment_state', '=', 'paid')])

            for odoo_invoice in odoo_paid_invoices:
                holded_invoice = self.env['holded_sync_odoo.odoo_invoices'].search(
                    [('invoiceNum', '=', odoo_invoice.name)])

                if holded_invoice and holded_invoice.holded_payment_state != '1':
                    holded_id = holded_invoice.holded_id
                    amount = odoo_invoice.amount_total
                    invoice_datetime = datetime.combine(odoo_invoice.create_date or fields.Date.today(),
                                                        datetime.min.time())
                    timestamp_date = int(invoice_datetime.timestamp())

                    url = f"https://api.holded.com/api/invoicing/v1/documents/invoice/{holded_id}/pay"

                    headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "key": "cf6626233fa4b33a99aa841dd37a11a9"
                    }

                    invoice_data = {
                        "amount": amount,
                        "date": timestamp_date,
                    }

                    response = requests.post(url, json=invoice_data, headers=headers)

                    if response.status_code == 200:
                        _logger.info(f"Invoice {holded_id} successfully paid in Holded")
                        holded_invoice.write({'holded_payment_state': '1'})
                    else:
                        _logger.error(f"Error paying invoice {holded_id} in Holded: {response.text}")

        except Exception as e:
            _logger.error(f"An error occurred while paying invoices in Holded: {e}")

    def bring_invoices_odoo(self):
        try:
            url = "https://api.holded.com/api/invoicing/v1/documents/invoice"
            headers = {
                "accept": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                invoices_list = response.json()
                odoo_invoices = self.env['holded_sync_odoo.odoo_invoices'].search([])
                existing_invoices = odoo_invoices
                existing_invoices.unlink()
                for invoice_data in invoices_list:
                    invoice_info = {
                        "holded_id": invoice_data.get('id'),
                        "contactName": invoice_data.get('contactName'),
                        "invoiceNum": invoice_data.get('docNumber'),
                        "holded_payment_state": invoice_data.get("status"),
                    }
                    self.env['holded_sync_odoo.odoo_invoices'].create(invoice_info)
        except Exception as e:
            _logger.error("An error occurred while bringing invoices from Holded to Odoo: %s", e)

    def update_invoices_odoo(self):
        try:
            url = "https://api.holded.com/api/invoicing/v1/documents/invoice"
            headers = {
                "accept": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                invoices_list = response.json()
                odoo_invoices = self.env['holded_sync_odoo.odoo_invoices'].search([])
                for invoice_data in invoices_list:

                    invoice_info = {
                        "holded_id": invoice_data.get('id'),
                        "contactName": invoice_data.get('contactName'),
                        "invoiceNum": invoice_data.get('docNumber'),
                        "holded_payment_state": invoice_data.get("status"),
                    }
                    invoice_exist = odoo_invoices.filtered(lambda i: i.invoiceNum == invoice_data.get('docNumber'))
                    if not invoice_exist:
                        self.env['holded_sync_odoo.odoo_invoices'].create(invoice_info)
                    else:
                        invoice_exist.write(invoice_info)
        except Exception as e:
            _logger.error("An error occurred while updating invoices from Holded to Odoo: %s", e)

    def sync_invoices_button(self):
        try:
            self.bring_invoices_odoo()
            self.insert_holded_invoices()
            self.update_invoices_odoo()
            self.pay_holded_invoices()
        except Exception as e:
            _logger.error("An error occurred while syncing invoices: %s", e)
