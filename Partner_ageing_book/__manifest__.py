# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Libro vencida por pagar/cobrar',
    'version': '15.0.1.1.7',
    'category': 'Accounting',
    'live_test_url': 'https://www.youtube.com/watch?v=gVQi9q9Rs-E&t=5s',
    'summary': """Dynamic Financial Reports with drill 
                down and filters– Community Edition""",
    'description': "Dynamic Financial Reports, DynamicFinancialReports, FinancialReport, Accountingreports, odoo reports, odoo"
                   "This module creates dynamic Accounting General Ledger, Trial Balance, Balance Sheet "
                   "Proft and Loss, Cash Flow Statements, Partner Ledger,"
                   "Partner Ageing, Day book"
                   "Bank book and Cash book reports in Odoo 14 community edition.",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'base_accounting_kit'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/views.xml',
        'views/kit_menus.xml',
        'report/ageing.xml',
    ],

    'assets': {
        'web.assets_backend': [
                'Partner_ageing_book/static/src/css/report.css',
                'Partner_ageing_book/static/src/js/action_manager.js',
                'Partner_ageing_book/static/src/js/ageing.js',
        ],
        'web.assets_qweb': [
            'Partner_ageing_book/static/src/xml/ageing.xml',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
