# -*- coding: utf-8 -*-

{
    'name': 'Account Invoice FEL -corposistemas-',
    'version': '1.0.1',
    'author': 'J2L Tech GT',
    'website': 'https://j2ltechgt.com', 
    'support': 'Luis Aquino --> laquinob@j2ltechgt.com', 
    'category': 'Accounting',
    'depends': ['account_invoice_fel_corposistemas', 'sale'],
    'summary': 'Transfer Invoice To Corposistemas And Receive Certificate',
    'data': [
        'views/sale_view.xml',
        'views/account_view.xml',
    ],
    'license': 'LGPL-3',
    'sequence': 1,
    'application': True,
    'installable': True,
    'auto_install': False,
}
