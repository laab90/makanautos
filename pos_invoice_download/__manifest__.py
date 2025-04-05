# -*- coding: utf-8 -*-

{
	'name': 'POS Invoice Download -MegaPrint-',
	'category': 'Point of Sale',
	'summary': 'Descargar binanrio de factura electronica firmada',
	'version': '1.0',
	'sequence': 1,
	'depends': ['point_of_sale', 'account_invoice_fel_corposistemas'],
	'author':'J2L Tech GT',
	'website': 'https://j2ltechgt.com',
	'support': 'Luis Aquino -> laquinob@j2ltechgt.com',
	'data': [
		'views/pos_order_views.xml',
	],
	'assets': {
        'point_of_sale.assets': [
            'pos_invoice_download/static/src/js/models.js',
        ],
    },
	'installable': True,
	'application': True,
	'auto_install': False,
}
