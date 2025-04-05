{
    'name': 'Facturas Reporte Excels',
    'version': '1.0',
    'description': 'Facturas de reportes en Excels mediante wizards',
    'author': 'RQ',
    'license': 'LGPL-3',
    'category': 'account',
    'auto_install': False,
    'depends': [
        'report_xlsx',
        'account',
        'crm'
    ],
    'data': [
        'security/security.xml',
        'views/invoice_sale.xml',
        'views/invoice_purchase.xml',
        'views/account_journal_view.xml',
        'views/menu.xml',
        'reports/report_action.xml'
    ],
    'installable': True
}
