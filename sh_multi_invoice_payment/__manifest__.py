# Copyright (C) Softhealer Technologies.
{
    "name": "Multiple Invoice Payment",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": "Multiple payment for invoice, customer multiple payment,Multiple Bill Payment, Mass credit note payment,Mass debit note Payment, Bunch invoice payment Odoo",
    "description": """Are you wasting your time by register payment one by one? This module will use to register payment for multiple invoices on a single click. Select multiple invoices and add payment info and you do! This module will register payment for customer invoices, vendor bills, debit notes, credit notes.""",
    "version": "14.0.1",
    "depends": [
        "account",
    ],
    "application": True,
    "data": [

        "security/ir.model.access.csv",
        "wizard/multi_invoice_payment.xml",

    ],
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 35,
    "currency": "EUR"
}
