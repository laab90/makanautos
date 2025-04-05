# -*- coding: utf-8 -*-

{
    'name': 'Electronic invoicing Guatemala FEL-G4S',
    'version': '1.0.1', 
    'category': 'Accounting',
    'description': """electronic invoicing in Guatemala""",
    'depends': ['account','l10n_gt','snailmail_account','account_tax_python'],
    'summary': 'Transfer Invoice To G4S And Receive Certificate',
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/satdte_frases_data.xml',
        'views/res_company_view.xml',
        'views/satdte_frases_view.xml',
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
        
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}