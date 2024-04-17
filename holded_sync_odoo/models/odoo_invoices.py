from odoo import models, fields

import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class Invoice(models.Model):
    _name = 'holded_sync_odoo.odoo_invoices'
    _description = 'Odoo internal invoices to be synchronized and exported to Holded ERP'

    holded_id = fields.Char(string='Holded Invoice ID')
    invoiceNum = fields.Char(string='Invoice Number')
    contactName = fields.Char(string='Customer Name')
    payment_state = fields.Char(string='Payment State')
    status = fields.Char(string='Payment Status')

    def insert_invoices(self):
        odoo_invoices = self.env['account.move'].search([])

        # _logger.info(len(odoo_invoices))
        # for odoo_invoice in odoo_invoices:
        #     _logger.info("%s , %s - %s" % (odoo_invoice.name, odoo_invoice.move_type, odoo_invoice.state))

        for odoo_invoice in odoo_invoices:
            if odoo_invoice.state != "draft" and odoo_invoice.move_type != "entry":
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
                    "contactName": odoo_invoice.partner_id.name
                }

                # Verificar si la factura ya existe en Holded
                holded_invoice_exists = self.env['holded_sync_odoo.odoo_invoices'].search([
                    ('invoiceNum', '=', odoo_invoice.name)
                ])

                if not holded_invoice_exists:
                    response = requests.post(url, json=invoice_data, headers=headers)
                    if response.status_code == 200:
                        _logger.info("Holded request for invoice %s: %s", odoo_invoice.id, response.text)
                    else:
                        _logger.error("Error inserting invoice %s in Holded: %s", odoo_invoice.id, response.text)
                else:
                    _logger.info("Invoice %s already exists in Holded, skipping insertion", odoo_invoice.name)

    def pay_invoices(self, holded_id):
        odoo_invoices = self.env['account.move'].search([])
        for odoo_invoice in odoo_invoices:
            if odoo_invoice and odoo_invoice.payment_state == 'paid':
                amount = odoo_invoice.amount_total

                invoice_dateduetime = datetime.combine(odoo_invoice.invoice_date_due or
                                                       fields.Date.today(),datetime.min.time())
                timestamp_datedue = int(invoice_dateduetime.timestamp())

                url = f"https://api.holded.com/api/invoicing/v1/documents/invoice/{holded_id}/pay"

                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "key": "cf6626233fa4b33a99aa841dd37a11a9"
                }

                invoice_data = {
                    "amount": amount,
                    "date": timestamp_datedue,
                }

                response = requests.post(url, json=invoice_data, headers=headers)

                if response.status_code == 200:
                    _logger.info("Invoice %s successfully paid in Holded", holded_id)
                else:
                    _logger.error("Error paying invoice %s in Holded: %s", holded_id, response.text)

    def bring_invoices_odoo(self):
        url = "https://api.holded.com/api/invoicing/v1/documents/invoice"
        headers = {
            "accept": "application/json",
            "key": "cf6626233fa4b33a99aa841dd37a11a9"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            invoices_list = response.json()
            odoo_invoices = self.env['holded_sync_odoo.odoo_invoices'].search([])

            # Eliminar todas las facturas existentes antes de insertar las nuevas
            existing_invoices = odoo_invoices.search([])
            existing_invoices.unlink()

            for invoice_data in invoices_list:
                invoice_info = {
                    "holded_id": invoice_data.get('id'),
                    "contactName": invoice_data.get('contactName'),
                    "invoiceNum": invoice_data.get('docNumber'),
                    "status": invoice_data.get('status'),
                }

                self.env['holded_sync_odoo.odoo_invoices'].create(invoice_info)

    def update_invoices_odoo(self):
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
                    "contactName":invoice_data.get('contactName'),
                    "invoiceNum": invoice_data.get('docNumber'),
                    "status": invoice_data.get('status'),
                }

                invoice_exist = odoo_invoices.filtered(lambda i: i.invoiceNum == invoice_data.get('docNumber'))
                if not invoice_exist:
                    self.env['holded_sync_odoo.odoo_invoices'].create(invoice_info)
                else:
                    invoice_exist.write(invoice_info)

    # Método para sincronizar las facturas al hacer clic en un botón
    def sync_invoices_button(self):
        self.bring_invoices_odoo()
        self.insert_invoices()
        self.update_invoices_odoo()

        holded_invoices_to_pay = self.env['holded_sync_odoo.odoo_invoices'].search([('invoiceNum', '!=', False)])
        for pay_holded_invoice in holded_invoices_to_pay:
            odoo_invoice = self.env['account.move'].search([('name', '=', pay_holded_invoice.invoiceNum)])
            if odoo_invoice and odoo_invoice.payment_state == 'paid':
                self.pay_invoices(pay_holded_invoice.holded_id)