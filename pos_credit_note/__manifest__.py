# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Credit Notes',
    'version': '1.01.1',
    'category': 'Point of Sale',
    'sequence': 1,
    'summary': 'POS Credit Notes',
    'description': "POS Credit Notes",
    'author':  "J2L Technologies GT",
    'support': "soporte@j2ltechgt.com",
    'depends': ['base_setup', 'point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
