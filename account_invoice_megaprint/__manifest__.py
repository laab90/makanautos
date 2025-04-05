# -*- coding: utf-8 -*-

{
    'name': 'Account Invoice FEL -MEGAPRINT',
    'version': '1.0.1',
    'author': 'Xetechs, S.A.',
    'website': 'https://www.xetechs.com', 
    'support': 'Luis Aquino --> laquino@xetechs.com', 
    'category': 'Accounting',
    'depends': ['account'],
    'summary': 'Transfer Invoice To MegaPrint And Receive Certificate',
    'data': [
        'data/invoice_cron.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/res_company_view.xml',
        'views/satdte_frases.xml',
        'views/account_journal_views.xml',
        'views/satdte_frases_data.xml',
        'wizard/wizard_cancel_view.xml',
        'reports/report_fel_format.xml',
        'reports/account_invoice_fel_format.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
