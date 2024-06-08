# -*- coding: utf-8 -*-
{
    'name': "Gestion de Proyectos",

    'summary': "Módulo personalizado para la gestión de proyectos en Odoo",

    'author': "Jose Miguel Garcia",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Custom',

    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/proyecto_views.xml',
        'views/tarea_views.xml',
        'views/coste_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml'
    ],
    'application':True,
    'sequence':1
}
