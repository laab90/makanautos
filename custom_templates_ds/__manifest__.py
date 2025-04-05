# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Custom_Report_Template_HN',
    'version': '1.0',
    'category': 'Accounting/Expenses',
    'sequence': 1,
    'summary': 'Custom Report Template -HN-',
    'description': """
Custom Report Template -HN-
============================
""",
    'website': 'https://www.odoo.com',
    'depends': ['base_setup', 'account','account_invoice_report_excel_rq'],
    'data': [
        'security/groups.xml',
        'views/account_invoice_view.xml',
        'reports/reports.xml',
        #'reports/report_invoice_srl.xml',
        'reports/report_invoice_hn.xml',
        #'reports/report_comprobante_sv.xml',
        #'reports/report_exportacion_sv.xml',
        #'reports/report_factura_sv.xml',
    ],
    'installable': True,
    'application': True,
}
