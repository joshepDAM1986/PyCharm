from odoo import models, fields, api

class Proyecto(models.Model):
    _name = 'gestion_proyectos.proyecto'
    _description = 'Proyecto'
    _order = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    imagen = fields.Binary(string='Imagen')
    prioridad = fields.Selection([
        ('minima', 'Mínima'),
        ('intermedia', 'Intermedia'),
        ('maxima', 'Máxima')],
        string='Prioridad')

    # Relacion Many2one con res.user que selecciona un jefe de proyecto
    usuario_id = fields.Many2one('res.users', string='Encargado')

    # Relacion One2many con tarea que muestra las tareas asociadas
    tareas_ids = fields.One2many('gestion_proyectos.tarea', 'proyecto_id', string='Tareas')

    # Muestra el numero de tareas completas
    tareas_completadas = fields.Integer(string='Tareas Completas', compute='_compute_tareas_completadas', store=True)
    @api.depends('tareas_ids', 'tareas_ids.completado')
    def _compute_tareas_completadas(self):
        for proyecto in self:
            proyecto.tareas_completadas = self.env['gestion_proyectos.tarea'].search_count(
                [('proyecto_id', '=', proyecto.id), ('completado', '=', True)])

    # Muestra el porcentaje de progreso del proyecto en funcion de tareas completadas
    progreso = fields.Float(string='Progreso', compute='_compute_progreso', store=True, digits=(3, 2))
    @api.depends('tareas_ids', 'tareas_ids.completado')
    def _compute_progreso(self):
        for proyecto in self:
            total_tareas = len(proyecto.tareas_ids)
            if total_tareas > 0:
                proyecto.progreso = (proyecto.tareas_completadas / total_tareas) * 100
            else:
                proyecto.progreso = 0

    # Muestra los costes relacionados al proyecto
    presupuestos_relacionados = fields.Many2many(
        'gestion_proyectos.coste', 'proyecto_coste_rel', 'proyecto_id', 'coste_id',
        string='Costes')

    # Muestra el total resultante de la suma de todos los presupuestos.
    total_presupuestos = fields.Float(string='Presupuesto', compute='_compute_total_presupuestos', store=True)
    @api.depends('presupuestos_relacionados.total')
    def _compute_total_presupuestos(self):
        for proyecto in self:
            proyecto.total_presupuestos = sum(proyecto.presupuestos_relacionados.mapped('total'))

    # Muestra el nombre de cada registro y no el numero de registros.
    proyecto_mostrar_nombres = fields.Char(string='Mostrar Nombres', compute='_compute_proyecto_mostrar_nombres', store=True)
    @api.depends('nombre')
    def _compute_proyecto_mostrar_nombres(self):
        for proyecto in self:
            proyecto.proyecto_mostrar_nombres = f"{proyecto.nombre}"

    # Sustituye la id del registro por su nombre al mostrar la relación
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.nombre}"))
        return result


