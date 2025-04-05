# -*- coding: utf-8 -*-


from odoo import fields, models, api
from odoo.exceptions import UserError, Warning

import logging

_logger = logging.getLogger( __name__ )

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    customer_vat = fields.Char('Customer Vat')
    customer_name = fields.Char('Customer Name')


    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        self.ensure_one()
        res.update({
            'customer_vat': self.customer_vat,
            'customer_name': self.customer_name,
        })
        return res