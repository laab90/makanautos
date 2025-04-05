# -*- coding: utf-8 -*-
{
	'name' : 'Fel infomation in POS',
	'author': "Elder",
	'version' : '15',
	'summary' : 'FEL Information in POS',
	'description' : 'FEL Information in POS Ticket',
	'depends' : ['point_of_sale'],
	'data' : ['views/view.xml'],
	'assets': {
        'web.assets_qweb': [
            	'pos_ticket_fel/static/src/xml/**/*'],
	'point_of_sale.assets': [
        	'pos_ticket_fel/static/src/js/Screens/pos_receipt_invoice_number.js'],
    },
	'demo' : [],
    'application': True,
    'sequence': 1,
	'installable' : True,
	'license': 'LGPL-3',
	'auto_install' : False,
}
