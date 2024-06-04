from odoo import models, fields, api


class Autosync(models.Model):
    _name = "holded_sync_odoo.autosync"
    _description = 'Holded Sync Odoo Auto Synchronization'

    @api.model
    def autosync_everything_button(self):
        product_model = self.env['holded_sync_odoo.odoo_products']
        customer_model = self.env['holded_sync_odoo.odoo_customers']
        treasuries_model = self.env['holded_sync_odoo.odoo_treasuries']
        taxes_model = self.env['holded_sync_odoo.odoo_taxes']
        payments_model = self.env['holded_sync_odoo.odoo_payments']
        invoices_model = self.env['holded_sync_odoo.odoo_invoices']
        creditnotes_model = self.env['holded_sync_odoo.odoo_creditnotes']
        purchases_model = self.env['holded_sync_odoo.odoo_purchases']
        refunds_model = self.env['holded_sync_odoo.odoo_refunds']

        product_model.insert_products()
        product_model.bring_products()

        customer_model.insert_customers()
        customer_model.bring_customers()

        treasuries_model.insert_treasuries()
        treasuries_model.bring_treasuries()

        taxes_model.bring_taxes()
        taxes_model.link_taxes()

        invoices_model.insert_holded_invoices()
        creditnotes_model.insert_holded_creditnotes()
        purchases_model.insert_holded_purchases()
        refunds_model.insert_holded_refunds()

        payments_model.bring_payments()

        invoices_model.pay_holded_invoices()
        creditnotes_model.pay_holded_creditnotes()
        purchases_model.pay_holded_purchases()
        refunds_model.pay_holded_refunds()

        payments_model.bring_payments()




