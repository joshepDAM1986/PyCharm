from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Refunds(models.Model):
    _name = 'odoo2holded.odoo_refunds'
    _description = 'Odoo refunds to be synchronized and exported to Holded ERP'

    holded_refund_id = fields.Char(string='Holded Refund ID')
    invoiceNum = fields.Char(string='Purchase Number')
    contactName = fields.Char(string='Customer Name')
    holded_payment_state = fields.Char(string='Payment State')
    holded_amount_total = fields.Float(string="Total")
    holded_payment_charged = fields.Float(string='Charged')
    holded_residual_payment = fields.Float(string='Residual')
    holded_payment_id = fields.Char(string="Holded Payment ID")
    last_sync = fields.Datetime(string='Last Sync', readonly=True, default=False)

    @property
    def holded_api_url(self):
        return "https://api.holded.com/api/invoicing/v1/documents/purchaserefund"

    @property
    def holded_api_headers(self):
        config = self.env['odoo2holded.apikeyconfig'].search([], limit=1)
        api_key = config.api_key if config else ''
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "key": api_key
        }

    def insert_holded_refunds(self):
        try:
            self.bring_refunds_odoo()
            odoo_refunds = self.env['account.move'].search([])
            batch_size = 100
            total_refunds = len(odoo_refunds)
            for index in range(0, total_refunds, batch_size):
                batch_refunds = odoo_refunds[index:index + batch_size]
                self.process_batch(batch_refunds)
            self.bring_refunds_odoo()
        except Exception as e:
            _logger.error("An error occurred inserting refunds into Holded: %s", e)

    def process_batch(self, batch_refunds):
        try:
            for odoo_refunds in batch_refunds:
                if (odoo_refunds.state != "draft"
                        and odoo_refunds.move_type != "entry"
                        and odoo_refunds.move_type == "in_refund"):

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
                            "taxes": self.get_holded_taxes(line.tax_ids)
                        } for line in odoo_refunds.invoice_line_ids],
                        "customFields": [{
                            "Factura": original_purchase
                        }],
                    }

                    _logger.info("Info sent to holded: %s", refund_data)

                    holded_refund_exists = self.env['odoo2holded.odoo_refunds'].search([
                        ('invoiceNum', '=', odoo_refunds.name)
                    ])
                    if not holded_refund_exists:
                        response = (
                            requests.post(self.holded_api_url, json=refund_data, headers=self.holded_api_headers))
                        if response.status_code == 200:
                            _logger.info("Refund %s successfully inserted: %s", odoo_refunds.id, response.text)
                        else:
                            _logger.error("Error processing refund %s in Holded: %s", odoo_refunds.id,
                                          response.text)
                    else:
                        _logger.info("Refund %s already exists in Holded", odoo_refunds.name)
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def get_holded_taxes(self, tax_ids):
        holded_tax_keys = []
        for tax in tax_ids:
            odoo_tax = self.env['odoo2holded.odoo_taxes'].search([('odoo_tax_id', '=', tax.id)], limit=1)
            if odoo_tax and odoo_tax.holded_tax_key:
                holded_tax_keys.append(odoo_tax.holded_tax_key)
        return holded_tax_keys

    def pay_holded_refunds(self):
        try:
            odoo_refunds = self.env['account.move'].search([('payment_state', '!=', 'not_paid')])

            batch_size = 100
            total_refunds = len(odoo_refunds)
            for index in range(0, total_refunds, batch_size):
                batch_refunds = odoo_refunds[index:index + batch_size]
                self.process_payment_batch(batch_refunds)
        except Exception as e:
            _logger.error(f"An error occurred while processing payments in Holded: {e}")

    def process_payment_batch(self, batch_refunds):
        try:
            for odoo_refunds in batch_refunds:
                holded_refunds = self.env['odoo2holded.odoo_refunds'].search(
                    [('invoiceNum', '=', odoo_refunds.name)])

                for holded_refund in holded_refunds:
                    if holded_refund.holded_payment_state == '1':
                        _logger.info("Holded refund %s is already fully paid", holded_refund.invoiceNum)
                        continue

                    holded_url_id = holded_refund.holded_refund_id

                    holded_treasury = self.env['odoo2holded.odoo_treasuries'].search(
                        [('name', '=', odoo_refunds.partner_id.bank_ids.bank_name)], limit=1)

                    if holded_treasury:
                        holded_payment_treasury_id = holded_treasury.holded_treasury_id
                    else:
                        holded_payment_treasury_id = None

                    odoo_refunds = self.env['account.move'].search([
                        ('name', '=', odoo_refunds.name),
                        ('state', '=', 'posted'),
                        ('move_type', '=', 'in_refund')
                    ])

                    for refund in odoo_refunds:
                        for odoo_payment in refund._get_reconciled_payments():
                            desc = f"{odoo_payment.id} {odoo_refunds.id}"

                            holded_payment_exists = self.env['odoo2holded.odoo_payments'].search([
                                ('odoo_document_id', "=", odoo_refunds.id),
                                ('odoo_payment_id', '=', odoo_payment.id),
                                ('contactName', '=', odoo_payment.partner_id.name),
                                ('amount', '=', odoo_payment.amount),
                            ])

                            if holded_payment_exists:
                                _logger.info("Payment %s for Holded invoice %s already processed", odoo_payment.name,
                                             holded_refund.invoiceNum)
                                continue

                            refund_datetime = datetime.combine(odoo_payment.date or fields.Date.today(),
                                                               datetime.min.time())
                            timestamp_date = int(refund_datetime.timestamp())

                            url = f"{self.holded_api_url}/{holded_url_id}/pay"

                            refund_data = {
                                "amount": odoo_payment.amount,
                                "date": timestamp_date,
                                "desc": desc
                            }

                            if odoo_payment.journal_id.type == "bank":
                                refund_data["treasury"] = holded_payment_treasury_id

                            response = requests.post(url, json=refund_data, headers=self.holded_api_headers)

                            if response.status_code == 200:
                                _logger.info(
                                    f"Payment {odoo_payment.id} successfully processed for Holded refund {holded_url_id}")
                            else:
                                _logger.error(
                                    f"Error processing payment {odoo_payment.id} for Holded refund {holded_url_id}: {response.text}")

        except Exception as e:
            _logger.error(f"An error occurred while processing payment batch: {e}")

    def bring_refunds_odoo(self):
        try:
            existing_refunds = self.env['odoo2holded.odoo_refunds'].search([])
            existing_refunds.unlink()

            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)

            if response.status_code == 200:
                refunds_list = response.json()

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

                    self.env['odoo2holded.odoo_refunds'].create(refund_info)

                self.sudo().search([], limit=1).write({'last_sync': fields.Datetime.now()})

        except Exception as e:
            _logger.error("An error occurred while bringing refunds from Holded to Odoo: %s", e)

    def sync_refunds_button(self):
        try:
            self.bring_refunds_odoo()
        except Exception as e:
            _logger.error("An error occurred while syncing refunds: %s", e)
