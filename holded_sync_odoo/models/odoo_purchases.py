from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Purchase(models.Model):
    _name = 'holded_sync_odoo.odoo_purchases'
    _description = 'Odoo purchases to be synchronized and exported to Holded ERP'

    holded_purchase_id = fields.Char(string='Holded Purchase ID')
    invoiceNum = fields.Char(string='Purchase Number')
    contactName = fields.Char(string='Supplier Name')
    holded_payment_state = fields.Char(string='Payment State')
    holded_amount_total = fields.Float(string="Total")
    holded_payment_charged = fields.Float(string='Charged')
    holded_residual_payment = fields.Float(string='Residual')
    last_sync = fields.Datetime(string='Last Sync', readonly=True, default=False)

    @property
    def holded_api_url(self):
        return "https://api.holded.com/api/invoicing/v1/documents/purchase"

    @property
    def holded_api_headers(self):
        config = self.env['holded.sync.odoo.apikeyconfig'].search([], limit=1)
        api_key = config.api_key if config else ''
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "key": api_key
        }

    def insert_holded_purchases(self):
        try:
            self.bring_purchases_odoo()
            odoo_purchases = self.env['account.move'].search([])
            batch_size = 100
            total_purchases = len(odoo_purchases)
            for index in range(0, total_purchases, batch_size):
                batch_purchases = odoo_purchases[index:index + batch_size]
                self.process_batch(batch_purchases)
            self.bring_purchases_odoo()
        except Exception as e:
            _logger.error("An error occurred inserting purchases into Holded: %s", e)

    def process_batch(self, batch_purchases ):
        try:
            for odoo_purchase in batch_purchases:
                if (odoo_purchase.state != "draft"
                        and odoo_purchase.move_type != "entry"
                        and odoo_purchase.move_type == "in_invoice"):

                    contact_code = odoo_purchase.partner_id.vat
                    purchase_datetime = datetime.combine(odoo_purchase.invoice_date or fields.Date.today(),
                                                         datetime.min.time())
                    timestamp_date = int(purchase_datetime.timestamp())
                    purchase_dateduetime = datetime.combine(odoo_purchase.invoice_date_due or fields.Date.today(),
                                                            datetime.min.time())
                    timestamp_datedue = int(purchase_dateduetime.timestamp())

                    purchase_data = {
                        "invoiceNum": odoo_purchase.name,
                        "contactCode": contact_code,
                        "date": timestamp_date,
                        "dueDate": timestamp_datedue,
                        "items": [{
                            "units": line.quantity,
                            "sku": line.product_id.code,
                            "subtotal": line.price_unit,
                            "taxes": self.get_holded_taxes(line.tax_ids)
                        } for line in odoo_purchase.invoice_line_ids],
                    }

                    _logger.info("Info sent to holded: %s", purchase_data)

                    holded_purchase_exists = self.env['holded_sync_odoo.odoo_purchases'].search([
                        ('invoiceNum', '=', odoo_purchase.name)
                    ])
                    if not holded_purchase_exists:
                        response = (
                            requests.post(self.holded_api_url, json=purchase_data, headers=self.holded_api_headers))
                        if response.status_code == 200:
                            _logger.info("Purchase %s successfully inserted: %s", odoo_purchase.id, response.text)
                        else:
                            _logger.error("Error processing purchase %s in Holded: %s", odoo_purchase.id, response.text)
                    else:
                        _logger.info("Purchase %s already exists in Holded", odoo_purchase.name)
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def get_holded_taxes(self, tax_ids):
        holded_tax_keys = []
        for tax in tax_ids:
            odoo_tax = self.env['holded_sync_odoo.odoo_taxes'].search([('odoo_tax_id', '=', tax.id)], limit=1)
            if odoo_tax and odoo_tax.holded_tax_key:
                holded_tax_keys.append(odoo_tax.holded_tax_key)
        return holded_tax_keys

    def pay_holded_purchases(self):
        try:
            odoo_purchases = self.env['account.move'].search([('payment_state', '!=', 'not_paid')])

            batch_size = 100
            total_purchases = len(odoo_purchases)
            for index in range(0, total_purchases, batch_size):
                batch_purchases = odoo_purchases[index:index + batch_size]
                self.process_payment_batch(batch_purchases)
        except Exception as e:
            _logger.error(f"An error occurred while paying purchases in Holded: {e}")

    def process_payment_batch(self, batch_purchases):
        try:
            for odoo_purchase in batch_purchases:
                holded_purchases = self.env['holded_sync_odoo.odoo_purchases'].search(
                    [('invoiceNum', '=', odoo_purchase.name)])

                for holded_purchase in holded_purchases:
                    if holded_purchase.holded_payment_state == '1':
                        _logger.info("Holded purchase %s is already fully paid", holded_purchase.invoiceNum)
                        continue

                    holded_url_id = holded_purchase.holded_purchase_id

                    holded_treasury = self.env['holded_sync_odoo.odoo_treasuries'].search(
                        [('name', '=', odoo_purchase.partner_id.bank_ids.bank_name)], limit=1)

                    if holded_treasury:
                        holded_payment_treasury_id = holded_treasury.holded_treasury_id
                    else:
                        holded_payment_treasury_id = None

                    odoo_payments = self.env['account.payment'].search([
                        ('ref', '=', odoo_purchase.name),
                        ('state', '=', 'posted'),
                        ('payment_type', '=', 'outbound'),
                        ('partner_id.name', '=',
                         odoo_purchase.partner_id.name)])

                    for odoo_payment in odoo_payments:
                        desc = f"{odoo_payment.id} {odoo_purchase.id}"

                        holded_payment_exists = self.env['holded_sync_odoo.odoo_payments'].search([
                            ('odoo_document_id', "=", odoo_purchase.id),
                            ('odoo_payment_id', '=', odoo_payment.id),
                            ('contactName', '=', odoo_payment.partner_id.name),
                            ('amount', '=', -odoo_payment.amount),
                        ])

                        if holded_payment_exists:
                            _logger.info("Payment %s for Holded purchase %s already processed", odoo_payment.id,
                                         holded_purchase.invoiceNum)
                            continue

                        purchase_datetime = datetime.combine(odoo_payment.date or fields.Date.today(),
                                                             datetime.min.time())
                        timestamp_date = int(purchase_datetime.timestamp())

                        url = f"{self.holded_api_url}/{holded_url_id}/pay"

                        purchase_data = {
                            "amount": odoo_payment.amount,
                            "date": timestamp_date,
                            "desc": desc
                        }

                        if odoo_payment.journal_id.type == 'bank':
                            purchase_data["treasury"] = holded_payment_treasury_id

                        response = requests.post(url, json=purchase_data, headers=self.holded_api_headers)

                        if response.status_code == 200:
                            _logger.info(
                                f"Payment {odoo_payment.id} successfully processed for Holded purchase {holded_url_id}")
                        else:
                            _logger.error(
                                f"Error processing payment {odoo_payment.id} for Holded purchase: {holded_url_id}: "
                                f"{response.text}")

        except Exception as e:
            _logger.error(f"An error occurred while processing payment batch: {e}")

    def bring_purchases_odoo(self):
        try:
            existing_purchases = self.env['holded_sync_odoo.odoo_purchases'].search([])
            existing_purchases.unlink()

            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)

            if response.status_code == 200:
                purchases_list = response.json()

                for purchase_data in purchases_list:
                    purchase_info = {
                        "holded_purchase_id": purchase_data.get('id'),
                        "contactName": purchase_data.get('contactName'),
                        "invoiceNum": purchase_data.get('docNumber'),
                        "holded_payment_state": purchase_data.get("status"),
                        "holded_amount_total": purchase_data.get("total"),
                        "holded_payment_charged": purchase_data.get("paymentsTotal"),
                        "holded_residual_payment": purchase_data.get("paymentsPending")
                    }

                    self.env['holded_sync_odoo.odoo_purchases'].create(purchase_info)

                self.sudo().search([], limit=1).write({'last_sync': fields.Datetime.now()})

        except Exception as e:
            _logger.error("An error occurred while bringing purchases from Holded to Odoo: %s", e)

    def sync_purchases_button(self):
        try:
            self.bring_purchases_odoo()
        except Exception as e:
            _logger.error("An error occurred while syncing purchases: %s", e)
