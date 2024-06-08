from odoo import models, fields, api

class Tarea(models.Model):
    _name = 'gestion_proyectos.tarea'
    _description = 'Gestor de tareas de proyectos'
    _order = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    vencimiento = fields.Date(string='Vencimiento')
    socios_ids = fields.Many2many('res.partner', string='Responsables Asignados')
    socios_nombres = fields.Char(string='Nombres de Responsables', compute='_compute_socios_nombres', store=True)
    proyecto_id = fields.Many2one('gestion_proyectos.proyecto', string='Proyecto Asignado')
    completado = fields.Boolean(string='Completado')

    # Muestra el nombre de cada registro y no el numero de registros.
    @api.depends('socios_ids')
    def _compute_socios_nombres(self):
        for tarea in self:
            tarea.socios_nombres = ', '.join(tarea.socios_ids.mapped('name'))

    # Sustituye la id del registro por su nombre al mostrar la relación
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.nombre))
        return result


