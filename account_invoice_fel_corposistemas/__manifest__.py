# -*- coding: utf-8 -*-

{
    'name': 'Account Invoice FEL -corposistemas-',
    'version': '1.0.1',
    'author': 'J2L Tech GT',
    'website': 'https://j2ltechgt.com', 
    'support': 'Luis Aquino --> laquinob@j2ltechgt.com', 
    'category': 'Accounting',
    'depends': ['account'],
    'summary': 'Transfer Invoice To Corposistemas And Receive Certificate',
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/res_company_view.xml',
        'views/satdte_frases.xml',
        'views/account_journal_views.xml',
        'views/satdte_frases_data.xml',
        'wizard/wizard_cancel_view.xml',
    ],
    "external_dependencies": {
        "python" : ['xmltodict']
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
