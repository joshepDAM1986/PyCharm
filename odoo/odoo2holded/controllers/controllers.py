# -*- coding: utf-8 -*-
# from odoo import http


# class HoldedSyncOdoo(http.Controller):
#     @http.route('/holded_sync_odoo/holded_sync_odoo', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/holded_sync_odoo/holded_sync_odoo/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('holded_sync_odoo.listing', {
#             'root': '/holded_sync_odoo/holded_sync_odoo',
#             'objects': http.request.env['holded_sync_odoo.holded_sync_odoo'].search([]),
#         })

#     @http.route('/holded_sync_odoo/holded_sync_odoo/objects/<model("holded_sync_odoo.holded_sync_odoo"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('holded_sync_odoo.object', {
#             'object': obj
#         })
