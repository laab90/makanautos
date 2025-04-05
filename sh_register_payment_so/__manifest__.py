# -*- coding: utf-8 -*-

{
    "name": "Register Payment From Sale",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Sales",
    "summary": """Sales Advance Payment App, Quotation Register Payment, Sale Order Quick Payment Module, Multiple Payment Single Invoice, Multiple So Multi Payment Single Invoice, Mange Quote Advance Payment, Make Sales Advance Payment Odoo.""",
    "description": """An Advance Payment means contractually due sum that is paid or received in advance for goods or services, while the balance included in the invoice. But in odoo, there is no feature for advance payment from the sale. This module will provide that feature. You can make register payment from sale while creating a quotation or sale order. It will also manage journal items, so you do not need to worry about journal management. You can also use advance payment from another sale order(*Only if both order have same customer).
 Register Payment On Sale Order, SO Advance Payment Odoo
 Advance Payment In Sales, Register Payment  In Quotation, Sale Order Quick Payment Module, Multiple Payment Single Invoice, Multiple So Multi Payment Single Invoice, Mange Advance Payment From Quote, Make Advance Payment In Sales  Odoo.
 Sales Advance Payment App, Quotation Register Payment, Sale Order Quick Payment Module, Multiple Payment Single Invoice, Multiple So Multi Payment Single Invoice, Mange Quote Advance Payment, Make Sales Advance Payment Odoo.""",
    "version": "10.0.2",
    "depends": ["sale", "account"],
    "data": [

        'security/payment_security.xml',
        'wizard/payment_wizard_views.xml',
        'views/sale_order_view.xml',
        'security/ir.model.access.csv'
    ],

    "images": ["static/description/background.png",],  
    "live_test_url": "https://youtu.be/qCHmQLdQRxM",            
    "auto_install":False,
    "installable": True,
    "application" : True,
    "price": 20,
    "currency": "EUR"    
} 
