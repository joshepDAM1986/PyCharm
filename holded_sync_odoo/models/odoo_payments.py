from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class Payment(models.Model):
    _name = 'holded_sync_odoo.odoo_payments'
    _description = 'Odoo payments to be synchronized and exported to Holded ERP'

    documentNum = fields.Char(string="Document Number")
    paymentNum = fields.Char(string="Payment Number")
    contact_name = fields.Char(string='Contact Name')
    amount = fields.Float(string='Amount')
    desc = fields.Char(string='Description')
    date = fields.Date(string="Date")
