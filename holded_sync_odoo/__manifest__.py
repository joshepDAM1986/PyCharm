# -*- coding: utf-8 -*-
{
    'name': "Holded Sync Odoo",
    'summary': """
        An Odoo module that is synchronized with Holded """,
    'description': """
        An Odoo module that is synchronized with Holded to import several data .
    """,
    'author': "WhiteWall Solutions",
    'website': "http://www.whitewallsolutions.com",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base','account'],
    'data': [
        'views/custom_products.xml',
        'views/odoo_products.xml',
        'views/odoo_customers.xml',
        'views/odoo_invoices.xml',
        'views/odoo_purchases.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'sequence': 1,
}