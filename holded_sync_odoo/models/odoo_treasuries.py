from odoo import models, fields
import requests
import logging

_logger = logging.getLogger(__name__)


class Treasury(models.Model):
    _name = 'holded_sync_odoo.odoo_treasuries'
    _description = 'Odoo internal treasuries to be synchronized and exported to Holded ERP'

    holded_id = fields.Char(string='Holded ID')
    name = fields.Char(string='Bank Name',)
    bic = fields.Char(string='BIC/SWIFT')
    acc_number = fields.Char(string='IBAN',)

    def insert_or_update_treasury(self, odoo_treasury, holded_treasuries):
        try:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }

            iban = False
            bank_name = odoo_treasury.name
            partner_bank = self.env['res.partner.bank'].search([('bank_name', '=', bank_name)])
            if partner_bank:
                iban = partner_bank.acc_number

            treasury_data = {
                "name": odoo_treasury.name,
                "type": "bank",
                "iban": iban,
                "swift": odoo_treasury.bic
            }

            holded_treasury = next(
                (treasury for treasury in holded_treasuries if treasury['name'] == odoo_treasury.name), None)

            if holded_treasury:
                url_update_holded_treasury = f"https://api.holded.com/api/invoicing/v1/treasury/{holded_treasury['id']}"
                response = requests.put(url_update_holded_treasury, headers=headers, json=treasury_data)
                if response.status_code == 200:
                    _logger.info("Updated treasury in Holded: %s", treasury_data)
                else:
                    _logger.error("Error while updating treasury in Holded: %s", response.text)
            else:
                url_create_holded_treasury = "https://api.holded.com/api/invoicing/v1/treasury"
                response = requests.post(url_create_holded_treasury, headers=headers, json=treasury_data)
                if response.status_code == 200:
                    holded_treasury_id = response.json().get('id')
                    odoo_treasury.write({'holded_id': holded_treasury_id})
                    _logger.info("Created treasury in Holded: %s", treasury_data)
                else:
                    _logger.error("Error while creating treasury in Holded: %s", response.text)
        except Exception as e:
            _logger.error("An error occurred while inserting or updating treasury in Holded: %s", e)

    def insert_treasuries(self):
        try:
            url_get_holded_treasuries = "https://api.holded.com/api/invoicing/v1/treasury"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }

            response = requests.get(url_get_holded_treasuries, headers=headers)
            holded_treasuries = response.json()

            odoo_treasuries = self.env['res.bank'].search([])
            for odoo_treasury in odoo_treasuries:
                self.insert_or_update_treasury(odoo_treasury, holded_treasuries)

        except Exception as e:
            _logger.error("An error occurred while inserting treasuries in Holded: %s", e)


    def bring_treasuries(self):
        try:
            url = "https://api.holded.com/api/invoicing/v1/treasury"
            headers = {
                "accept": "application/json",
                "key": "cf6626233fa4b33a99aa841dd37a11a9"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                holded_treasuries = response.json()
                odoo_treasuries = self.env['holded_sync_odoo.odoo_treasuries'].search([])

                for treasury_data in holded_treasuries:
                    treasury_exist = odoo_treasuries.filtered(lambda t: t.name == treasury_data.get('name'))
                    treasury_info = {
                        "holded_id": treasury_data.get('id'),
                        "name": treasury_data.get('name'),
                        "acc_number": treasury_data.get('iban'),
                        "bic": treasury_data.get('swift'),
                    }

                    if not treasury_exist:
                        self.env['holded_sync_odoo.odoo_treasuries'].create(treasury_info)
                    else:
                        treasury_exist.write(treasury_info)
            else:
                _logger.error("Error while fetching treasuries from Holded: %s", response.text)
        except Exception as e:
            _logger.error("An error occurred while bringing treasuries from Holded to Odoo: %s", e)

    def sync_treasuries_button(self):
        try:
            self.insert_treasuries()
            self.bring_treasuries()
        except Exception as e:
            _logger.error("An error occurred while syncing treasuries: %s", e)