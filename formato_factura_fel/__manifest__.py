# -*- coding: utf-8 -*-

{
    'name': "Formato Factura Fel",

    'summary': """Imprime la factura en formato Fel.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "J2LTechGt",
    'website': "https://www.j2ltechgt.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales/Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'num_to_words'],

    # always loaded
    'data': [
        'report/factura_fel.xml',
        'report/reports.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'license': 'LGPL-3',
}
