# -*- coding: utf-8 -*-
# from odoo import http


# class GestionProyectos(http.Controller):
#     @http.route('/gestion_proyectos/gestion_proyectos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gestion_proyectos/gestion_proyectos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('gestion_proyectos.listing', {
#             'root': '/gestion_proyectos/gestion_proyectos',
#             'objects': http.request.env['gestion_proyectos.gestion_proyectos'].search([]),
#         })

#     @http.route('/gestion_proyectos/gestion_proyectos/objects/<model("gestion_proyectos.gestion_proyectos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gestion_proyectos.object', {
#             'object': obj
#         })
