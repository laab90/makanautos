# -*- encoding: UTF-8 -*-
##############################################################################
#
# Copyright (C) 2018-Today J2L Tech GT
# (<https://j2ltechgt.odoo.com>)
#
##############################################################################

{
    "name": "Partner Multicompany",
    "summary": "Partner Multicompany",
    'description': """
Partner Multicompany
    * default company user
    * others

    """,
    'author': "J2L Tech GT",
    'website': "https://j2ltechgt.odoo.com",
    'support': "soporte@j2ltechgt.com",
    "version": "1.0",
    "category": "Tools",
    "depends": ['base', 'base_setup', 'sale', 'account', 'analytic'],
    "data": [
        'views/res_partner_view.xml',
        'views/account_analytic_view.xml',
        ],
    'sequence': 1,
    'installable': True,
    'auto_install': False,
    'application': True,
}
