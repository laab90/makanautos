# -*- coding: utf-8 -*-
{
  'name': "Odoo Woocommerce Connector, Multiple Woocommerce store connection, Import Customer, Orders, Products data - Odoo wordpress woocommerce Connector, Bi-directional data exchange between WooCommerce and Odoo",
'version': '15.0.0.3',
   'summary': "Odoo Woocommerce Connector, odoo and woocommerce data import in odoo, Multiple Woocommerce store connection, Import Customer Data, Orders, Products, woocommerce Connector Odoo, Woocommerce odoo connector, woocommerce integration odoo, connect woocommerce",

   'description':"""
       Odoo Woocommerce Connector is bridge between odoo and woocommerce data import in odoo, Odoo Woocommerce Connector, Multiple Woocommerce store connection, Import Customer Data, Orders, Products, Odoo woocommerce wordpress Connector
     odoo15, odoo 14, odoo 13, odoo 12, odoo 11.""",


  "depends"  :  ['odoo_multi_connect_sales_aagam'],
  "data"   :  [
            'security/ir.model.access.csv',
             'wizard/import_update_wizard.xml',
             'wizard/export_template.xml',
             'views/woc_config_views.xml',
             'data/import_cron.xml',
             'views/inherited_woocommerce_dashboard_view.xml',
             
             'data/default_data.xml',

            ],

    'application': True,
    'price': 110,
    'currency': 'USD',
    'support': ': business@aagaminfotech.com',
    'author': 'Aagam Infotech',
    'website': 'http://aagaminfotech.com',
    'license': 'OPL-1',
    'images': ['static/description/images/Banner.gif'],
    "external_dependencies":  {'python': ['woocommerce']},
}
