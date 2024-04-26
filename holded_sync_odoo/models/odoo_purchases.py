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

    def insert_holded_purchases(self):
        try:
            odoo_purchases = self.env['account.move'].search([])
            batch_size = 100
            total_purchases = len(odoo_purchases)
            for index in range(0, total_purchases, batch_size):
                batch_purchases = odoo_purchases[index:index + batch_size]
                self.process_batch(batch_purchases)
        except Exception as e:
            _logger.error("An error occurred while inserting purchases into Holded: %s", e)

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
                            "subtotal": line.price_subtotal / line.quantity,
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
                            _logger.error("Error inserting purchase %s in Holded: %s", odoo_purchase.id, response.text)
                    else:
                        _logger.info("Purchase %s already exists in Holded, skipping insertion", odoo_purchase.name)
        except Exception as e:
            _logger.error("An error occurred while processing batch: %s", e)

    def pay_holded_purchases(self):
        try:
            odoo_paid_purchases = self.env['account.move'].search([('payment_state', '!=', 'not_paid')])

            for odoo_purchase in odoo_paid_purchases:
                holded_purchase = self.env['holded_sync_odoo.odoo_purchases'].search(
                    [('invoiceNum', '=', odoo_purchase.name)])

                if holded_purchase and holded_purchase.holded_payment_state != '1':  # Verificar que no esté ya pagada en Holded
                    holded_id = holded_purchase.holded_id
                    amount_paid = odoo_purchase.amount_total - odoo_purchase.amount_residual
                    amount_pending = odoo_purchase.amount_residual
                    purchase_datetime = datetime.combine(odoo_purchase.create_date or fields.Date.today(),
                                                         datetime.min.time())
                    timestamp_date = int(purchase_datetime.timestamp())

                    url = f"https://api.holded.com/api/invoicing/v1/documents/purchase/{holded_id}/pay"

                    headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "key": "cf6626233fa4b33a99aa841dd37a11a9"
                    }

                    purchase_data = {
                        "amount": amount_paid,
                        "date": timestamp_date,
                    }

                    response = requests.post(url, json=purchase_data, headers=headers)

                    if response.status_code == 200:
                        _logger.info(f"Purchase {holded_id} successfully paid in Holded")
                        if amount_pending > 0:
                            holded_purchase.write(
                                {'holded_payment_state': '2'})
                        else:
                            holded_purchase.write(
                                {'holded_payment_state': '1'})
                    else:
                        _logger.error(f"Error paying purchase {holded_id} in Holded: {response.text}")

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
                odoo_purchases = self.env['holded_sync_odoo.odoo_purchases'].search([])
                existing_purchases = odoo_purchases
                existing_purchases.unlink()
                for purchase_data in purchases_list:
                    purchase_info = {
                        "holded_id": purchase_data.get('id'),
                        "contactName": purchase_data.get('contactName'),
                        "invoiceNum": purchase_data.get('docNumber'),
                        "holded_payment_state": purchase_data.get("status"),
                    }
                    self.env['holded_sync_odoo.odoo_purchases'].create(purchase_info)
        except Exception as e:
            _logger.error("An error occurred while bringing purchases from Holded to Odoo: %s", e)

    def update_purchases_odoo(self):
        try:
            url = "https://api.holded.com/api/invoicing/v1/documents/purchase"
            headers = {
                "accept": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                purchases_list = response.json()
                odoo_purchases = self.env['holded_sync_odoo.odoo_purchases'].search([])
                for purchase_data in purchases_list:

                    purchase_info = {
                        "holded_id": purchase_data.get('id'),
                        "contactName": purchase_data.get('contactName'),
                        "invoiceNum": purchase_data.get('docNumber'),
                        "holded_payment_state": purchase_data.get("status"),
                    }
                    purchase_exist = odoo_purchases.filtered(lambda p: p.invoiceNum == purchase_data.get('docNumber'))
                    if not purchase_exist:
                        self.env['holded_sync_odoo.odoo_purchases'].create(purchase_info)
                    else:
                        purchase_exist.write(purchase_info)
        except Exception as e:
            _logger.error("An error occurred while updating purchases from Holded to Odoo: %s", e)

    def sync_purchases_button(self):
        try:
            self.bring_purchases_odoo()
            self.insert_holded_purchases()
            self.update_purchases_odoo()
            self.pay_holded_purchases()
        except Exception as e:
            _logger.error("An error occurred while syncing purchases: %s", e)