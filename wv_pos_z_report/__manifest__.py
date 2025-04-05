# -*- coding: utf-8 -*-

{
    'name': 'POS Z Report',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Allows you to print Z report by thermal printer and normal printer.',
    'description': "Allows you to print Z report by thermal printer and normal printer",
    'depends': ['point_of_sale'],
    'data': [
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'wv_pos_z_report/static/src/js/pos.js',
        ],
        'web.assets_qweb': [
            'wv_pos_z_report/static/src/xml/**/*',
        ],
    },
    'images': [
        'static/description/r1.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 35,
    'currency': 'USD',
}
