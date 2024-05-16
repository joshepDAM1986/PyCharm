from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Refunds(models.Model):
    _name = 'holded_sync_odoo.odoo_refunds'
    _description = 'Odoo refunds to be synchronized and exported to Holded ERP'

    holded_refund_id = fields.Char(string='Holded Refund ID')
    invoiceNum = fields.Char(string='Purchase Number')
    contactName = fields.Char(string='Customer Name')
    holded_payment_state = fields.Char(string='Payment State')
    holded_amount_total = fields.Float(string="Total")
    holded_payment_charged = fields.Float(string='Charged')
    holded_residual_payment = fields.Float(string='Residual')

    def insert_holded_refunds(self):
        try:
            self.bring_refunds_odoo()
            odoo_refunds = self.env['account.move'].search([])
            batch_size = 100
            total_refunds = len(odoo_refunds)
            for index in range(0, total_refunds, batch_size):
                batch_refunds = odoo_refunds[index:index + batch_size]
                self.process_batch(batch_refunds)
        except Exception as e:
            _logger.error("An error occurred inserting refunds into Holded: %s", e)

    def process_batch(self, batch_refunds):
        try:
            for odoo_refunds in batch_refunds:
                if (odoo_refunds.state != "draft"
                        and odoo_refunds.move_type != "entry"
                        and odoo_refunds.move_type == "in_refund"):
                    url = "https://api.holded.com/api/invoicing/v1/documents/purchaserefund"

                    headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "key": "cf6626233fa4b33a99aa841dd37a11a9"
                    }

                    contact_code = odoo_refunds.partner_id.vat
                    refunds_datetime = datetime.combine(odoo_refunds.invoice_date or fields.Date.today(),
                                                        datetime.min.time())
                    timestamp_date = int(refunds_datetime.timestamp())
                    refunds_dateduetime = datetime.combine(odoo_refunds.invoice_date_due or fields.Date.today(),
                                                           datetime.min.time())
                    timestamp_datedue = int(refunds_dateduetime.timestamp())

                    original_purchase = odoo_refunds.ref

                    refund_data = {
                        "invoiceNum": odoo_refunds.name,
                        "contactCode": contact_code,
                        "date": timestamp_date,
                        "dueDate": timestamp_datedue,
                        "items": [{
                            "units": line.quantity,
                            "sku": line.product_id.code,
                            "subtotal": line.price_unit,
                            "tax": sum(tax.amount for tax in line.tax_ids)
                        } for line in odoo_refunds.invoice_line_ids],
                        "customFields": [{
                            "Factura": original_purchase
                        }],
                    }

                    _logger.info("Info sent to holded: %s", refund_data)

                    holded_refund_exists = self.env['holded_sync_odoo.odoo_refunds'].search([
                        ('invoiceNum', '=', odoo_refunds.name)
                    ])
                    if not holded_refund_exists:
                        response = requests.post(url, json= refund_data, headers=headers)
                        if response.status_code == 200:
                            _logger.info("Refund %s successfully inserted: %s", odoo_refunds.id, response.text)
                        else:
                            _logger.error("Error processing refund %s in Holded: %s", odoo_refunds.id,
                                          response.text)
                    else:
                        _logger.info("Refund %s already exists in Holded", odoo_refunds.name)
            self.bring_refunds_odoo()
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def pay_holded_refunds(self):
        try:
            odoo_refunds = self.env['account.move'].search([('payment_state', '!=', 'not_paid')])

            batch_size = 100
            total_refunds = len(odoo_refunds)
            for index in range(0, total_refunds, batch_size):
                batch_refunds = odoo_refunds[index:index + batch_size]
                self.process_payment_batch(batch_refunds)

            self.bring_refunds_odoo()

        except Exception as e:
            _logger.error(f"An error occurred while processing payments in Holded: {e}")

    def process_payment_batch(self, batch_refunds):
        try:
            for odoo_refunds in batch_refunds:
                holded_refunds = self.env['holded_sync_odoo.odoo_refunds'].search(
                    [('invoiceNum', '=', odoo_refunds.name)])

                for holded_refund in holded_refunds:
                    if holded_refund.holded_payment_state == '1':
                        _logger.info("Holded refund %s is already fully paid", holded_refund.invoiceNum)
                        continue

                    holded_url_id = holded_refund.holded_refund_id

                    holded_treasury = self.env['holded_sync_odoo.odoo_treasuries'].search(
                        [('name', '=', odoo_refunds.partner_id.bank_ids.bank_name)], limit=1)

                    if holded_treasury:
                        holded_payment_treasury_id = holded_treasury.holded_treasury_id
                    else:
                        holded_payment_treasury_id = None

                    odoo_payments = self.env['account.payment'].search([
                                                                        ('state', '=', 'posted'),
                                                                        ('payment_type', '=', 'inbound'),
                                                                        ('partner_id.name', '=',
                                                                         odoo_refunds.partner_id.name)
                    ])

                    for odoo_payment in odoo_payments:
                        holded_payment_exists = self.env['holded_sync_odoo.odoo_payments'].search_count([
                            ('processed_payment', '=', 'Processed'),
                            ('documentNum', '=', odoo_refunds.name),
                            ('paymentNum', '=', odoo_payment.name),
                            ('contact_name', '=', odoo_payment.partner_id.name),
                            ('amount', '=', odoo_payment.amount),
                            ('date', '=', odoo_payment.date),
                        ])

                        if holded_payment_exists:
                            _logger.info("Payment %s for Holded invoice %s already processed", odoo_payment.name,
                                         holded_refund.invoiceNum)
                            continue

                        refund_datetime = datetime.combine(odoo_payment.date or fields.Date.today(),
                                                           datetime.min.time())
                        timestamp_date = int(refund_datetime.timestamp())

                        url = f"https://api.holded.com/api/invoicing/v1/documents/purchaserefund/{holded_url_id}/pay"

                        headers = {
                            "accept": "application/json",
                            "content-type": "application/json",
                            "key": "cf6626233fa4b33a99aa841dd37a11a9"
                        }

                        refund_data = {
                            "amount": odoo_payment.amount,
                            "date": timestamp_date,
                        }

                        if odoo_payment.journal_id.type == "bank":
                            refund_data["treasury"] = holded_payment_treasury_id

                        response = requests.post(url, json=refund_data, headers=headers)

                        if response.status_code == 200:
                            _logger.info(
                                f"Payment {odoo_payment.id} successfully processed for Holded refund {holded_url_id}")

                            new_payment = self.env['holded_sync_odoo.odoo_payments'].create({
                                'documentNum': odoo_refunds.name,
                                'paymentNum': odoo_payment.name,
                                'contact_name': odoo_refunds.partner_id.name,
                                'amount': odoo_payment.amount,
                                'date': odoo_payment.date,
                                'processed_payment': 'Processed'
                            })

                        else:
                            _logger.error(
                                f"Error processing payment {odoo_payment.id} for Holded refund {holded_url_id}: {response.text}")

        except Exception as e:
            _logger.error(f"An error occurred while processing payment batch: {e}")

    def bring_refunds_odoo(self):
        try:

            url = "https://api.holded.com/api/invoicing/v1/documents/purchaserefund"
            headers = {
                "accept": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                refunds_list = response.json()
                existing_refunds = self.env['holded_sync_odoo.odoo_refunds'].search([])

                for refund_data in refunds_list:
                    refund_info = {
                        "holded_refund_id": refund_data.get('id'),
                        "contactName": refund_data.get('contactName'),
                        "invoiceNum": refund_data.get('docNumber'),
                        "holded_payment_state": refund_data.get("status"),
                        "holded_amount_total": refund_data.get("total"),
                        "holded_payment_charged": refund_data.get("paymentsTotal"),
                        "holded_residual_payment": refund_data.get("paymentsPending")
                    }

                    refund_exist = existing_refunds.filtered(
                        lambda i: i.invoiceNum == refund_info.get('invoiceNum'))
                    if refund_exist:
                        refund_exist.write(refund_info)
                    else:
                        self.env['holded_sync_odoo.odoo_refunds'].create(refund_info)
        except Exception as e:
            _logger.error("An error occurred while bringing refunds from Holded to Odoo: %s", e)

    def sync_refunds_button(self):
        try:
            self.insert_holded_refunds()
            self.pay_holded_refunds()
        except Exception as e:
            _logger.error("An error occurred while syncing refunds: %s", e)