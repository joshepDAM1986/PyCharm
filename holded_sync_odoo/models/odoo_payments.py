from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class Payment(models.Model):
    _name = 'holded_sync_odoo.odoo_payments'
    _description = 'Odoo payments to be synchronized and exported to Holded ERP'

    holded_payment_id = fields.Char(string='Holded Payment ID')
    contact_id = fields.Char(string="Contact ID")
    contact_name = fields.Char(string='Contact Name')
    amount = fields.Float(string='Amount')
    desc = fields.Char(string='Description')
    date = fields.Date(string="Date")
    treasury = fields.Char(string="Treasury ID")
    processed_payment = fields.Char(string="Processed", default="Not Processed")