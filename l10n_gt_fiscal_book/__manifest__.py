# -*- coding: utf-8 -*-
{
    'name': "Libros de Compras/Ventas -GT-",

    'summary': """Añade reportes de libro de ventas y compras para localizacion guatemalteca""",

    'description': """
    1.- Configuracion general para contabilidad guatemalteca
    2.- Impuestos adicionales al iva para libro de ventas y compras
    3.- Libro de Ventas del IVA
    4.- Libro de Compras del IVA
    5.- Otras generalidades de la contabilidad guatemalteca
    
    """,

    'author': 'J2L Tech GT',
    'support': 'soporte@j2ltechgt.com',
    'website': "http://j2ltechgt.com",
    'category': 'Accounting',
    'version': '0.01.1',
    'license': "AGPL-3",    
    'depends': ['account', 'l10n_gt', 'l10n_gt_settings_account', 'account_invoice_fel_corposistemas'],
    "external_dependencies": {"python": ["xlwt"]},
    'data': [
        'data/data.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/account_move_type_view.xml',
        'views/account_move_view.xml',
        'wizard/wizard_fiscal_book_view.xml',
        'reports/reports.xml',
        'reports/layout.xml',
        'reports/report_sale_fiscal_book_tmpl.xml',
        'reports/report_purchase_fiscal_book_tmpl.xml',
        
    ],
}
