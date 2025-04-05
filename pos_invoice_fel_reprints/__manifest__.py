# -*- coding: utf-8 -*-

{
    'name': 'POS Order Invoice Reprint -G4S-',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 1,
    'author': 'J2L Technologies GT',
    'website': 'https://www.j2ltechgt.com',
    'support': 'soporte@j2ltechgt.com',
    'summary': "POS Order Invoice Reprint",
    'description': """POS Order Invoice Reprint""",
    'depends': ['pos_orders_lists', 'pos_ticket_fel_g4s'],
    'data': [
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_invoice_fel_reprints/static/src/js/pos.js',
        ],
        'web.assets_qweb': [
            'pos_invoice_fel_reprints/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
