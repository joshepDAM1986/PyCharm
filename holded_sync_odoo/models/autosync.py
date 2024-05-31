from odoo import models, fields


class Autosync(models.Model):
    _name = "holded_sync_odoo.autosync"
    _description = 'Holded Sync Odoo Auto Synchronization'

    def autosync_everything_button(self):
        product_model = self.env['holded_sync_odoo.odoo_products']
        product_model.insert_products()
        product_model.bring_products()

        customer_model = self.env['holded_sync_odoo.odoo_customers']
        customer_model.insert_customers()
        customer_model.bring_customers()

        treasuries_model = self.env['holded_sync_odoo.odoo_treasuries']
        treasuries_model.insert_treasuries()
        treasuries_model.bring_treasuries()

        taxes_model = self.env['holded_sync_odoo.odoo_taxes']
        treasuries_model.bring_treasuries()
        taxes_model.link_taxes()

        payments_model = self.env['holded_sync_odoo.odoo_payments']

        invoices_model = self.env['holded_sync_odoo.odoo_invoices']
        invoices_model.insert_holded_invoices()
        payments_model.clear_payments()
        payments_model.bring_payments()
        invoices_model.pay_holded_invoices()
        payments_model.clear_payments()
        payments_model.bring_payments()

        creditnotes_model = self.env['holded_sync_odoo.odoo_creditnotes']
        creditnotes_model.insert_holded_creditnotes()
        payments_model.clear_payments()
        payments_model.bring_payments()
        creditnotes_model.pay_holded_creditnotes()
        payments_model.clear_payments()
        payments_model.bring_payments()

        purchases_model = self.env['holded_sync_odoo.odoo_purchases']
        purchases_model.insert_holded_purchases()
        payments_model.clear_payments()
        payments_model.bring_payments()
        purchases_model.pay_holded_purchases()
        payments_model.clear_payments()
        payments_model.bring_payments()

        refunds_model = self.env['holded_sync_odoo.odoo_refunds']
        refunds_model.insert_holded_refunds()
        payments_model.clear_payments()
        payments_model.bring_payments()
        refunds_model.pay_holded_refunds()
        payments_model.clear_payments()
        payments_model.bring_payments()


