from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class Purchase(models.Model):
    _name = 'holded_sync_odoo.odoo_purchases'
    _description = 'Odoo internal purchases to be synchronized and exported to Holded ERP'

    holded_id = fields.Char(string='Holded Purchase ID')
    invoiceNum = fields.Char(string='Purchase Num')
    contactName = fields.Char(string='Supplier Name')
    holded_payment_state = fields.Char(string='Payment State')
    holded_amount_total = fields.Float(string="Total")
    holded_payment_charged = fields.Float(string='Charged')
    holded_residual_payment = fields.Float(string='Residual')

    def insert_holded_purchases(self):
        try:
            self.bring_purchases_odoo()
            odoo_purchases = self.env['account.move'].search([])
            batch_size = 100
            total_purchases = len(odoo_purchases)
            for index in range(0, total_purchases, batch_size):
                batch_purchases = odoo_purchases[index:index + batch_size]
                self.process_batch(batch_purchases)
        except Exception as e:
            _logger.error("An error occurred inserting purchases into Holded: %s", e)

    def process_batch(self, batch_purchases ):
        try:
            for odoo_purchase in batch_purchases:
                if (odoo_purchase.state != "draft"
                        and odoo_purchase.move_type != "entry"
                        and odoo_purchase.move_type == "in_invoice"):
                    url = f"https://api.holded.com/api/invoicing/v1/documents/purchase"

                    headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "key": "cf6626233fa4b33a99aa841dd37a11a9"
                    }

                    contact_code = odoo_purchase.partner_id.vat
                    purchase_datetime = datetime.combine(odoo_purchase.invoice_date or fields.Date.today(),
                                                         datetime.min.time())
                    purchase_dateduetime = datetime.combine(odoo_purchase.invoice_date_due or fields.Date.today(),
                                                            datetime.min.time())
                    timestamp_date = int(purchase_datetime.timestamp())
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
                            "tax": sum(tax.amount for tax in line.tax_ids)
                        } for line in odoo_purchase.invoice_line_ids],
                    }

                    _logger.info("Info sent to holded: %s", purchase_data)

                    holded_purchase_exists = self.env['holded_sync_odoo.odoo_purchases'].search([
                        ('invoiceNum', '=', odoo_purchase.name)
                    ])
                    if not holded_purchase_exists:
                        response = requests.post(url, json=purchase_data, headers=headers)
                        if response.status_code == 200:
                            _logger.info("Purchase %s successfully inserted: %s", odoo_purchase.id, response.text)
                        else:
                            _logger.error("Error processing purchase %s in Holded: %s", odoo_purchase.id, response.text)
                    else:
                        _logger.info("Purchase %s already exists in Holded", odoo_purchase.name)
            self.bring_purchases_odoo()
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def pay_holded_purchases(self):
        try:
            odoo_purchases = self.env['account.move'].search([('payment_state', '!=', 'not_paid')])

            for odoo_purchase in odoo_purchases:
                holded_purchases = self.env['holded_sync_odoo.odoo_purchases'].search(
                    [('invoiceNum', '=', odoo_purchase.name)])

                for holded_purchase in holded_purchases:
                    if holded_purchase.holded_payment_state == '1':
                        # Si la factura en Holded ya está totalmente pagada, omitir el procesamiento
                        _logger.info("Holded purchase %s is already fully paid", holded_purchase.invoiceNum)
                        continue

                    holded_id = holded_purchase.holded_id

                    odoo_payments = self.env['account.payment'].search(
                        [('ref', '=', odoo_purchase.name),
                         ('state', '=', 'posted'),
                         ('payment_type', '=', 'outbound'),
                         ('partner_id.name', '=', odoo_purchase.partner_id.name)])

                    for odoo_payment in odoo_payments:
                        # Verificar si este pago ya ha sido procesado y registrado en Holded
                        holded_payment_exists = self.env['holded_sync_odoo.odoo_payments'].search_count([
                            ('holded_id', '=', holded_id),
                            ('amount', '=', odoo_payment.amount),
                            ('date', '=', odoo_payment.date),
                            ('processed_payment', '=', 'Processed')
                        ])

                        if holded_payment_exists:
                            _logger.info("Payment %s for Holded purchase %s already processed", odoo_payment.id,
                                         holded_purchase.invoiceNum)
                            continue

                        # Procesar el pago en Holded
                        invoice_datetime = datetime.combine(odoo_payment.date or fields.Date.today(),
                                                            datetime.min.time())
                        timestamp_date = int(invoice_datetime.timestamp())

                        url = f"https://api.holded.com/api/invoicing/v1/documents/purchase/{holded_id}/pay"

                        headers = {
                            "accept": "application/json",
                            "content-type": "application/json",
                            "key": "cf6626233fa4b33a99aa841dd37a11a9"
                        }

                        purchase_data = {
                            "amount": odoo_payment.amount,
                            "date": timestamp_date,
                        }

                        response = requests.post(url, json=purchase_data, headers=headers)

                        if response.status_code == 200:
                            _logger.info(
                                f"Payment {odoo_payment.id} successfully processed for Holded purchase {holded_id}")

                            new_payment = self.env['holded_sync_odoo.odoo_payments'].create({
                                'holded_id': holded_id,
                                'amount': odoo_payment.amount,
                                'date': odoo_payment.date,
                                'processed_payment': 'Processed'
                            })
                        else:
                            _logger.error(
                                f"Error processing payment {odoo_payment.id} "
                                f"for Holded purchase: {holded_id}: "
                                f"{response.text}")

            self.bring_purchases_odoo()

        except Exception as e:
            _logger.error(f"An error occurred while paying purchases in Holded: {e}")

    def bring_purchases_odoo(self):
        try:
            url = "https://api.holded.com/api/invoicing/v1/documents/purchase"
            headers = {
                "accept": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                purchases_list = response.json()
                existing_purchases = self.env['holded_sync_odoo.odoo_purchases'].search([])

                for purchase_data in purchases_list:
                    purchase_info = {
                        "holded_id": purchase_data.get('id'),
                        "contactName": purchase_data.get('contactName'),
                        "invoiceNum": purchase_data.get('docNumber'),
                        "holded_payment_state": purchase_data.get("status"),
                        "holded_amount_total": purchase_data.get("total"),
                        "holded_payment_charged": purchase_data.get("paymentsTotal"),
                        "holded_residual_payment": purchase_data.get("paymentsPending")
                    }

                    purchase_exist = existing_purchases.filtered(
                        lambda p: p.invoiceNum == purchase_info.get('invoiceNum'))
                    if purchase_exist:
                        purchase_exist.write(purchase_info)
                    else:
                        self.env['holded_sync_odoo.odoo_purchases'].create(purchase_info)
        except Exception as e:
            _logger.error("An error occurred while bringing purchases from Holded to Odoo: %s", e)

    def sync_purchases_button(self):
        try:
            self.insert_holded_purchases()
            self.pay_holded_purchases()
        except Exception as e:
            _logger.error("An error occurred while syncing purchases: %s", e)