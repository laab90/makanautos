# -*- coding: utf-8 -*-

{
    'name': 'Electronic invoicing Guatemala FEL-G4S Extends',
    'version': '1.0.1',
    'category': 'Accounting',
    'description': """Extending functionality of the electronic invoicing in Guatemala""",
    'depends': ['account', 'l10n_gt_fel_g4s'],
    'summary': 'Transfer Invoice To G4S And Receive Certificate',
    'data': [
        'views/account_move_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}