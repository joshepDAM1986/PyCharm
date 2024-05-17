from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Creditnotes(models.Model):
    _name = 'holded_sync_odoo.odoo_creditnotes'
    _description = 'Odoo credit notes to be synchronized and exported to Holded ERP'

    holded_creditnote_id = fields.Char(string='Holded Credit Note ID')
    invoiceNum = fields.Char(string='Invoice Number')
    contactName = fields.Char(string='Customer Name')
    holded_payment_state = fields.Char(string='Payment State')
    holded_amount_total = fields.Float(string="Total")
    holded_payment_charged = fields.Float(string='Charged')
    holded_residual_payment = fields.Float(string='Residual')

    @property
    def holded_api_url(self):
        return "https://api.holded.com/api/invoicing/v1/documents/creditnote"

    @property
    def holded_api_headers(self):
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

    def insert_holded_creditnotes(self):
        try:
            self.bring_creditnotes_odoo()
            odoo_creditnotes = self.env['account.move'].search([])
            batch_size = 100
            total_creditnotes = len(odoo_creditnotes)
            for index in range(0, total_creditnotes, batch_size):
                batch_creditnotes = odoo_creditnotes[index:index + batch_size]
                self.process_batch(batch_creditnotes)
        except Exception as e:
            _logger.error("An error occurred inserting credit notes into Holded: %s", e)

    def process_batch(self, batch_creditnotes):
        try:
            for odoo_creditnotes in batch_creditnotes:
                if (odoo_creditnotes.state != "draft"
                        and odoo_creditnotes.move_type != "entry"
                        and odoo_creditnotes.move_type == "out_refund"):

                    contact_code = odoo_creditnotes.partner_id.vat
                    creditnote_datetime = datetime.combine(odoo_creditnotes.invoice_date or fields.Date.today(),
                                                           datetime.min.time())
                    timestamp_date = int(creditnote_datetime.timestamp())
                    creditnote_dateduetime = datetime.combine(odoo_creditnotes.invoice_date_due or fields.Date.today(),
                                                              datetime.min.time())
                    timestamp_datedue = int(creditnote_dateduetime.timestamp())

                    original_invoice = odoo_creditnotes.ref

                    invoice_taxes = []
                    for line in odoo_creditnotes.invoice_line_ids:
                        tax_names = []
                        for tax in line.tax_ids:
                            tax_name = "s_" + tax.amount_type + "_" + str(int(tax.amount * 100))
                            tax_names.append(tax_name)
                        invoice_taxes.append(",".join(tax_names))

                    creditnote_data = {
                        "invoiceNum": odoo_creditnotes.name,
                        "contactCode": contact_code,
                        "date": timestamp_date,
                        "dueDate": timestamp_datedue,
                        "items": [{
                            "units": line.quantity,
                            "sku": line.product_id.code,
                            "subtotal": line.price_unit,
                            "tax": sum(tax.amount for tax in line.tax_ids),
                        } for line in odoo_creditnotes.invoice_line_ids],
                        "customFields": [{
                            "Factura": original_invoice
                        }],
                    }

                    _logger.info("Info sent to holded: %s", creditnote_data)

                    holded_creditnote_exists = self.env['holded_sync_odoo.odoo_creditnotes'].search([
                        ('invoiceNum', '=', odoo_creditnotes.name)
                    ])
                    if not holded_creditnote_exists:
                        response = (
                            requests.post(self.holded_api_url, json=creditnote_data, headers=self.holded_api_headers))
                        if response.status_code == 200:
                            _logger.info("Credit note %s successfully inserted: %s", odoo_creditnotes.id, response.text)
                        else:
                            _logger.error("Error processing credit note %s in Holded: %s", odoo_creditnotes.id,
                                          response.text)
                    else:
                        _logger.info("Credit note %s already exists in Holded", odoo_creditnotes.name)
            self.bring_creditnotes_odoo()
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def pay_holded_creditnotes(self):
        try:
            odoo_creditnotes = self.env['account.move'].search([('payment_state', '!=', 'not_paid')])

            batch_size = 100
            total_creditnotes = len(odoo_creditnotes)
            for index in range(0, total_creditnotes, batch_size):
                batch_creditnotes = odoo_creditnotes[index:index + batch_size]
                self.process_payment_batch(batch_creditnotes)

            self.bring_creditnotes_odoo()

        except Exception as e:
            _logger.error(f"An error occurred while processing payments in Holded: {e}")

    def process_payment_batch(self, batch_creditnotes):
        try:
            for odoo_creditnotes in batch_creditnotes:
                holded_creditnotes = self.env['holded_sync_odoo.odoo_creditnotes'].search(
                    [('invoiceNum', '=', odoo_creditnotes.name)])

                for holded_creditnote in holded_creditnotes:
                    if holded_creditnote.holded_payment_state == '1':
                        _logger.info("Holded credit note %s is already fully paid", holded_creditnote.invoiceNum)
                        continue

                    holded_url_id = holded_creditnote.holded_creditnote_id

                    holded_treasury = self.env['holded_sync_odoo.odoo_treasuries'].search(
                        [('name', '=', odoo_creditnotes.partner_id.bank_ids.bank_name)], limit=1)

                    if holded_treasury:
                        holded_payment_treasury_id = holded_treasury.holded_treasury_id
                    else:
                        holded_payment_treasury_id = None

                    odoo_payments = self.env['account.payment'].search([
                                                                        ('state', '=', 'posted'),
                                                                        ('payment_type', '=', 'outbound'),
                                                                        ('partner_id.name', '=',
                                                                         odoo_creditnotes.partner_id.name)
                    ])

                    for odoo_payment in odoo_payments:
                        holded_payment_exists = self.env['holded_sync_odoo.odoo_payments'].search_count([
                            ('processed_payment', '=', 'Processed'),
                            ('documentNum', '=', odoo_creditnotes.name),
                            ('paymentNum', '=', odoo_payment.name),
                            ('contact_name', '=', odoo_payment.partner_id.name),
                            ('amount', '=', odoo_payment.amount),
                            ('date', '=', odoo_payment.date),
                        ])

                        if holded_payment_exists:
                            _logger.info("Payment %s for Holded invoice %s already processed", odoo_payment.name,
                                         holded_creditnote.invoiceNum)
                            continue

                        creditnote_datetime = datetime.combine(odoo_payment.date or fields.Date.today(),
                                                               datetime.min.time())
                        timestamp_date = int(creditnote_datetime.timestamp())

                        url = f"{self.holded_api_url}/{holded_url_id}/pay"

                        creditnote_data = {
                            "amount": odoo_payment.amount,
                            "date": timestamp_date,
                        }

                        if odoo_payment.journal_id.type == "bank":
                            creditnote_data["treasury"] = holded_payment_treasury_id

                        response = requests.post(url, json=creditnote_data, headers=self.holded_api_headers)

                        if response.status_code == 200:
                            _logger.info(
                                f"Payment {odoo_payment.id} successfully processed for Holded credit note {holded_url_id}")

                            new_payment = self.env['holded_sync_odoo.odoo_payments'].create({
                                'documentNum': odoo_creditnotes.name,
                                'paymentNum': odoo_payment.name,
                                'contact_name': odoo_creditnotes.partner_id.name,
                                'amount': odoo_payment.amount,
                                'date': odoo_payment.date,
                                'processed_payment': 'Processed'
                            })

                        else:
                            _logger.error(
                                f"Error processing payment {odoo_payment.id} for Holded credit note {holded_url_id}: {response.text}")

        except Exception as e:
            _logger.error(f"An error occurred while processing payment batch: {e}")

    def bring_creditnotes_odoo(self):
        try:
            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)

            if response.status_code == 200:
                creditnotes_list = response.json()
                existing_creditnotes = self.env['holded_sync_odoo.odoo_creditnotes'].search([])

                for creditnote_data in creditnotes_list:
                    creditnote_info = {
                        "holded_creditnote_id": creditnote_data.get('id'),
                        "contactName": creditnote_data.get('contactName'),
                        "invoiceNum": creditnote_data.get('docNumber'),
                        "holded_payment_state": creditnote_data.get("status"),
                        "holded_amount_total": creditnote_data.get("total"),
                        "holded_payment_charged": creditnote_data.get("paymentsTotal"),
                        "holded_residual_payment": creditnote_data.get("paymentsPending")
                    }

                    creditnote_exist = existing_creditnotes.filtered(
                        lambda i: i.invoiceNum == creditnote_info.get('invoiceNum'))
                    if creditnote_exist:
                        creditnote_exist.write(creditnote_info)
                    else:
                        self.env['holded_sync_odoo.odoo_creditnotes'].create(creditnote_info)
        except Exception as e:
            _logger.error("An error occurred while bringing credit notes from Holded to Odoo: %s", e)

    def sync_creditnotes_button(self):
        try:
            self.insert_holded_creditnotes()
            self.pay_holded_creditnotes()
        except Exception as e:
            _logger.error("An error occurred while syncing credit notes: %s", e)