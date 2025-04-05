# -*- coding: utf-8 -*-
{
    'name': "Libros Financieros Contables",

    'summary': """Añade reportes financieros contables""",
    'description': """
Añade reportes financieros contables:
    * Libro Diarios
    * Libro Mayor
    * Balance de Situacion
    
    """,
    'author': 'J2L Tech GT',
    'website': "https://j2ltechgt.com",
    'support': 'soporte@j2ltechgt.com',
    'category': 'Accounting',
    'version': '0.01.1',
    'depends': ['account', 'l10n_gt'],
    'license': "AGPL-3",
    "external_dependencies": {"python": ["xlwt"]},
    'data': [
        'views/general_ledger_line_template.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_financial_report_view.xml',
        'report/template_folio.xml',
        'report/layouts.xml',
        'report/layout.xml',
        'report/report_journal_ledger_tmpl.xml',
        'report/daily_general_ledger.xml',
        'wizard/trial_balance.xml',
        'report/report_trial_balance.xml',
        'report/reports.xml',
        'wizard/wizard_folio_general_ledger.xml',
    ],
}
