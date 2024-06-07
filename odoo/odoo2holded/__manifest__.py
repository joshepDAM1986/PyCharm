# -*- coding: utf-8 -*-
{
    'name': "odoo2holded",
    'summary': """
        An Odoo module that is synchronized with Holded """,
    'description': """
        An Odoo module that is synchronized with Holded to import several data .
    """,
    'author': "WhiteWall Software",
    'website': "https://whitewall-ers.com",
    'category': 'Accounting',
    'version': '1.0',
    'license': 'OPL-1',
    'depends': ['base'],
    'data': [
        'views/odoo_products.xml',
        'views/odoo_customers.xml',
        'views/odoo_invoices.xml',
        'views/odoo_purchases.xml',
        'views/odoo_payments.xml',
        'views/odoo_treasuries.xml',
        'views/odoo_creditnotes.xml',
        'views/odoo_refunds.xml',
        'views/odoo_taxes.xml',
        'views/apikeyconfig.xml',
        'views/autosync.xml',
        'data/ir_cron_data.xml',
    ],
    'application': True,
    'sequence': 1,
}