# -*- coding: utf-8 -*-
{
	'name' : 'Fel infomation in POS',
	'author': "J2L Technologies GT",
	'support': 'soporte@j2ltechgt.com',
	'version' : '15.01.1',
	'summary' : 'FEL Information in POS',
	'description' : 'FEL Information in POS Ticket',
	'depends' : ['point_of_sale', 'l10n_gt_fel_g4s'],
	'data' : ['views/view.xml'],
	'assets': {
        'web.assets_qweb': [
            	'pos_ticket_fel_g4s/static/src/xml/**/*'],
	'point_of_sale.assets': [
        	'pos_ticket_fel_g4s/static/src/js/Screens/pos_receipt_invoice_number.js'],
    },
	'demo' : [],
    'application': True,
    'sequence': 1,
	'installable' : True,
	'license': 'LGPL-3',
	'auto_install' : False,
}
