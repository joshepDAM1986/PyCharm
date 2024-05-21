from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HoldedSyncOdooConfig(models.Model):
    _name = 'holded.sync.odoo.apikeyconfig'
    _description = 'Holded Sync Odoo Api Key'

    api_key = fields.Char(string='API Key', required=True)

    @api.model
    def create(self, vals):
        if self.search_count([]) >= 1:
            raise ValidationError("Only one API Key configuration is allowed at a time")
        return models.Model.create(self, vals)

    def write(self, vals):
        if self.search_count([]) > 1:
            raise ValidationError("Only one API Key configuration is allowed at a time")
        return models.Model.write(self, vals)

    def save_api_key(self):
        return {'type': 'ir.actions.act_window_close'}
