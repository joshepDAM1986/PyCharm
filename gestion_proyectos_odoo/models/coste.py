from odoo import models, fields, api

class Coste(models.Model):
    _name = 'gestion_proyectos.coste'
    _description = 'Gestor de costes de proyectos'
    _order = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    presupuesto = fields.Float(string='Costes')
    iva = fields.Float(string='IVA')

    # Cálculo del presupuesto mas el IVA indicado
    total = fields.Float(string='Total', compute='_compute_calculo', store=True)
    @api.depends('presupuesto', 'iva')
    def _compute_calculo(self):
        for coste in self:
            coste.total = coste.presupuesto + (coste.presupuesto * coste.iva / 100)

    # Relacion Many2many con la clase proyecto
    proyectos_relacionados = fields.Many2many(
        'gestion_proyectos.proyecto', 'proyecto_coste_rel', 'coste_id', 'proyecto_id', string='Proyectos Asignados')

    # Muestra el nombre de cada registro y no el numero de registros.
    @api.depends('proyectos_relacionados.proyecto_display_name')
    def _compute_proyectos_relacionados_nombres(self):
        for coste in self:
            coste.proyectos_relacionados_nombres = ', '.join(
                coste.proyectos_relacionados.mapped('nombre'))

    # Sustituye la id del registro por su nombre al mostrar la relación
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.nombre))
        return result

