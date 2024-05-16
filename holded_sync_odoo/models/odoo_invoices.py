from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Invoice(models.Model):
    _name = 'holded_sync_odoo.odoo_invoices'
    _description = 'Odoo invoices to be synchronized and exported to Holded ERP'

    holded_invoice_id = fields.Char(string='Holded Invoice ID')
    invoiceNum = fields.Char(string='Invoice Number')
    contactName = fields.Char(string='Customer Name')
    holded_payment_state = fields.Char(string='Payment State')
    holded_amount_total = fields.Float(string="Total")
    holded_payment_charged = fields.Float(string='Charged')
    holded_residual_payment = fields.Float(string='Residual')

    def insert_holded_invoices(self):
        try:
            self.bring_invoices_odoo()
            odoo_invoices = self.env['account.move'].search([])
            batch_size = 100
            total_invoices = len(odoo_invoices)
            for index in range(0, total_invoices, batch_size):
                batch_invoices = odoo_invoices[index:index + batch_size]
                self.process_batch(batch_invoices)
        except Exception as e:
            _logger.error("An error occurred inserting invoices into Holded: %s", e)

    def process_batch(self, batch_invoices):
        try:
            for odoo_invoice in batch_invoices:
                if (odoo_invoice.state != "draft"
                        and odoo_invoice.move_type != "entry"
                        and odoo_invoice.move_type == "out_invoice"):
                    url = "https://api.holded.com/api/invoicing/v1/documents/invoice"

                    headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "key": "cf6626233fa4b33a99aa841dd37a11a9"
                    }

                    contact_code = odoo_invoice.partner_id.vat
                    invoice_datetime = datetime.combine(odoo_invoice.invoice_date or fields.Date.today(),
                                                        datetime.min.time())
                    timestamp_date = int(invoice_datetime.timestamp())
                    invoice_dateduetime = datetime.combine(odoo_invoice.invoice_date_due or fields.Date.today(),
                                                           datetime.min.time())
                    timestamp_datedue = int(invoice_dateduetime.timestamp())

                    invoice_data = {
                        "invoiceNum": odoo_invoice.name,
                        "contactCode": contact_code,
                        "date": timestamp_date,
                        "dueDate": timestamp_datedue,
                        "items": [{
                            "units": line.quantity,
                            "sku": line.product_id.code,
                            "subtotal": line.price_unit,
                            "tax": sum(tax.amount for tax in line.tax_ids)
                        } for line in odoo_invoice.invoice_line_ids],
                    }

                    _logger.info("Info sent to holded: %s", invoice_data)

                    holded_invoice_exists = self.env['holded_sync_odoo.odoo_invoices'].search([
                        ('invoiceNum', '=', odoo_invoice.name)
                    ])
                    if not holded_invoice_exists:
                        response = requests.post(url, json=invoice_data, headers=headers)
                        if response.status_code == 200:
                            _logger.info("Invoice %s successfully inserted: %s", odoo_invoice.id, response.text)
                        else:
                            _logger.error("Error processing invoice %s in Holded: %s", odoo_invoice.id, response.text)
                    else:
                        _logger.info("Invoice %s already exists in Holded", odoo_invoice.name)
            self.bring_invoices_odoo()
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def pay_holded_invoices(self):
        try:
            odoo_invoices = self.env['account.move'].search([('payment_state', '!=', 'not_paid')])

            batch_size = 100
            total_invoices = len(odoo_invoices)
            for index in range(0, total_invoices, batch_size):
                batch_invoices = odoo_invoices[index:index + batch_size]
                self.process_payment_batch(batch_invoices)

            self.bring_invoices_odoo()

        except Exception as e:
            _logger.error(f"An error occurred while processing payments in Holded: {e}")

    def process_payment_batch(self, batch_invoices):
        try:
            for odoo_invoice in batch_invoices:
                holded_invoices = self.env['holded_sync_odoo.odoo_invoices'].search(
                    [('invoiceNum', '=', odoo_invoice.name)])

                for holded_invoice in holded_invoices:
                    if holded_invoice.holded_payment_state == '1':
                        _logger.info("Holded invoice %s is already fully paid", holded_invoice.invoiceNum)
                        continue

                    holded_url_id = holded_invoice.holded_invoice_id

                    holded_treasury = self.env['holded_sync_odoo.odoo_treasuries'].search(
                        [('name', '=', odoo_invoice.partner_id.bank_ids.bank_name)], limit=1)

                    if holded_treasury:
                        holded_payment_treasury_id = holded_treasury.holded_treasury_id
                    else:
                        holded_payment_treasury_id = None

                    odoo_payments = self.env['account.payment'].search([('ref', '=', odoo_invoice.payment_reference),
                                                                        ('state', '=', 'posted'),
                                                                        ('payment_type', '=', 'inbound'),
                                                                        ('partner_id.name', '=',
                                                                         odoo_invoice.partner_id.name)])

                    for odoo_payment in odoo_payments:
                        holded_payment_exists = self.env['holded_sync_odoo.odoo_payments'].search_count([
                            ('processed_payment', '=', 'Processed'),
                            ('documentNum', '=', odoo_invoice.name),
                            ('paymentNum', '=', odoo_payment.name),
                            ('contact_name', '=', odoo_payment.partner_id.name),
                            ('amount', '=', odoo_payment.amount),
                            ('date', '=', odoo_payment.date),
                        ])

                        if holded_payment_exists:
                            _logger.info("Payment %s for Holded invoice %s already processed", odoo_payment.id,
                                         holded_invoice.invoiceNum)
                            continue

                        invoice_datetime = datetime.combine(odoo_payment.date or fields.Date.today(),
                                                            datetime.min.time())
                        timestamp_date = int(invoice_datetime.timestamp())

                        url = f"https://api.holded.com/api/invoicing/v1/documents/invoice/{holded_url_id}/pay"

                        headers = {
                            "accept": "application/json",
                            "content-type": "application/json",
                            "key": "cf6626233fa4b33a99aa841dd37a11a9"
                        }

                        invoice_data = {
                            "amount": odoo_payment.amount,
                            "date": timestamp_date,
                        }

                        if odoo_payment.journal_id.type == "bank":
                            invoice_data["treasury"] = holded_payment_treasury_id

                        response = requests.post(url, json=invoice_data, headers=headers)

                        if response.status_code == 200:
                            _logger.info(
                                f"Payment {odoo_payment.id} successfully processed for Holded invoice {holded_url_id}")

                            new_payment = self.env['holded_sync_odoo.odoo_payments'].create({
                                'documentNum': odoo_invoice.name,
                                'paymentNum': odoo_payment.name,
                                'contact_name': odoo_invoice.partner_id.name,
                                'amount': odoo_payment.amount,
                                'date': odoo_payment.date,
                                'processed_payment': 'Processed'
                            })

                        else:
                            _logger.error(
                                f"Error processing payment {odoo_payment.id} for Holded invoice {holded_url_id}: {response.text}")

        except Exception as e:
            _logger.error(f"An error occurred while processing payment batch: {e}")

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
                existing_invoices = self.env['holded_sync_odoo.odoo_invoices'].search([])

                for invoice_data in invoices_list:
                    invoice_info = {
                        "holded_invoice_id": invoice_data.get('id'),
                        "contactName": invoice_data.get('contactName'),
                        "invoiceNum": invoice_data.get('docNumber'),
                        "holded_payment_state": invoice_data.get("status"),
                        "holded_amount_total": invoice_data.get("total"),
                        "holded_payment_charged": invoice_data.get("paymentsTotal"),
                        "holded_residual_payment": invoice_data.get("paymentsPending")
                    }

                    invoice_exist = existing_invoices.filtered(
                        lambda i: i.invoiceNum == invoice_info.get('invoiceNum'))
                    if invoice_exist:
                        invoice_exist.write(invoice_info)
                    else:
                        self.env['holded_sync_odoo.odoo_invoices'].create(invoice_info)
        except Exception as e:
            _logger.error("An error occurred while bringing invoices from Holded to Odoo: %s", e)

    def sync_invoices_button(self):
        try:
            self.insert_holded_invoices()
            self.pay_holded_invoices()
        except Exception as e:
            _logger.error("An error occurred while syncing invoices: %s", e)