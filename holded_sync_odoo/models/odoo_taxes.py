from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class HoldedTax(models.Model):
    _name = 'holded_sync_odoo.holded_tax'
    _description = 'Holded Tax'

    key = fields.Char(string='Holded Tax Key')
    name = fields.Char(string='Holded Tax Name')
    amount = fields.Float(string='Holded Tax Amount')
    scope = fields.Char(string='Holded Tax Scope')
    group = fields.Char(string='Holded Tax Group')
    type = fields.Char(string='Holded Tax Type')


class OdooTaxes(models.Model):
    _name = 'holded_sync_odoo.odoo_taxes'
    _description = 'Taxes Attachment'

    odoo_tax_id = fields.Many2one('account.tax', string='Odoo Taxes')
    holded_tax_id = fields.Many2one('holded_sync_odoo.holded_tax', string='Holded Taxes')
    holded_tax_key = fields.Char(related='holded_tax_id.key', string='Holded Taxes Key', store=True)
    last_sync = fields.Datetime(string='Last Sync', readonly=True, default=False)

    @property
    def holded_api_url(self):
        return "https://api.holded.com/api/invoicing/v1/taxes"

    @property
    def holded_api_headers(self):
        config = self.env['holded.sync.odoo.apikeyconfig'].search([], limit=1)
        api_key = config.api_key if config else ''
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "key": api_key
        }

    def bring_taxes(self):
        try:
            response = requests.get(self.holded_api_url, headers=self.holded_api_headers)
            if response.status_code == 200:
                tax_list = response.json()

                for tax_data in tax_list:
                    tax_info = {
                        "key": tax_data.get('key'),
                        "name": tax_data.get('name'),
                        "amount": tax_data.get('amount'),
                        "scope": tax_data.get('scope'),
                        "group": tax_data.get('group'),
                        "type": tax_data.get('type'),
                    }

                    holded_tax = self.env['holded_sync_odoo.holded_tax'].search([('key', '=', tax_info['key'])], limit=1)
                    if not holded_tax:
                        holded_tax = self.env['holded_sync_odoo.holded_tax'].create(tax_info)
                    else:
                        holded_tax.write(tax_info)

                    odoo_tax = self.env['holded_sync_odoo.odoo_taxes'].search([('holded_tax_id', '=', holded_tax.id)], limit=1)
                    if not odoo_tax:
                        self.env['holded_sync_odoo.odoo_taxes'].create({'holded_tax_id': holded_tax.id})
            else:
                _logger.error("Error while fetching taxes from Holded: %s", response.text)

            self.sudo().search([], limit=1).write({'last_sync': fields.Datetime.now()})

        except Exception as e:
            _logger.error("An error occurred while bringing taxes from Holded to Odoo: %s", e)

    @api.model
    def link_taxes(self):
        try:
            tax_mapping = self.env['holded_sync_odoo.maptaxes'].TAXES_MAPPING

            for odoo_tax_id, holded_tax_key in tax_mapping.items():
                odoo_tax = self.env['account.tax'].browse(odoo_tax_id)

                if odoo_tax:
                    odoo_tax_attachments = self.search([('holded_tax_key', '=', holded_tax_key)])
                    if odoo_tax_attachments:
                        odoo_tax_attachments.write({
                            'odoo_tax_id': odoo_tax.id,
                        })
                else:
                    _logger.warning(f"Odoo tax not found for ID: {odoo_tax_id}")

        except Exception as e:
            _logger.error("An error occurred while linking taxes: %s", e)

    def sync_taxes_button(self):
        try:
            self.bring_taxes()
            self.link_taxes()
        except Exception as e:
            _logger.error("An error occurred while syncing invoices: %s", e)
