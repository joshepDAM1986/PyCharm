from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HoldedSyncOdooConfig(models.Model):
    _name = 'odoo2holded.apikeyconfig'
    _description = 'Odoo module configuration'

    api_key = fields.Char(string='API Key', required=True)
    interval_number = fields.Integer(string='Cron Interval Number', default=1, help='Number of intervals')
    interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')
    ], string='Cron Interval Type', default='hours', required=True, help='Interval unit in the space of time')
    nextcall = fields.Datetime(string='Next Call', help='Date (dd/mm/YYYY) and Hour (hh:mm:ss')
    numbercall = fields.Integer(string='Number of Calls', default=-1, help='Number of repetitions (-1 for unlimited)')
    active = fields.Boolean(string='Active', default=True, help='Activate/Deactivate the Cron Job')

    @api.model
    def create(self, vals):
        if self.search_count([]) >= 1:
            raise ValidationError("Only one API Key configuration is allowed at a time")
        record = super(HoldedSyncOdooConfig, self).create(vals)
        record.update_cron_job()
        return record

    def write(self, vals):
        res = super(HoldedSyncOdooConfig, self).write(vals)
        self.update_cron_job()
        return res

    def update_cron_job(self):
        cron = self.env.ref('odoo2holded.ir_cron_autosync_everything', raise_if_not_found=False)
        if not cron:
            cron = self.env['ir.cron'].create({
                'name': 'Auto Sync Everything',
                'model_id': self.env.ref('odoo2holded.model_odoo2holded_autosync').id,
                'state': 'code',
                'code': 'model.autosync_everything_button()',
                'user_id': self.env.ref('base.user_root').id,
                'interval_type': self.interval_type,
                'interval_number': self.interval_number,
                'nextcall': self.nextcall,
                'numbercall': self.numbercall,
                'active': self.active,
            })
        else:
            cron.write({
                'interval_type': self.interval_type,
                'interval_number': self.interval_number,
                'nextcall': self.nextcall,
                'numbercall': self.numbercall,
                'active': self.active,
            })

    def save_api_key(self):
        self.update_cron_job()
        return {'type': 'ir.actions.act_window_close'}
