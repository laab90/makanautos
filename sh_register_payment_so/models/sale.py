# -*- coding: utf-8 -*-

from odoo import api,fields,models

class SaleOrder(models.Model):
    """ Inherited Sale Order to add account_payment_ids field and calculate resisual amount """

    _inherit = "sale.order"

    def _get_amount_residual(self):
        advance_amount = 0.0
        for line in self.sh_account_payment_ids:
            if line.state != 'draft':
                advance_amount += line.amount
        self.sh_amount_resisual = self.amount_total - advance_amount - self.discount_total

    sh_account_payment_ids = fields.One2many('account.payment', 'sale_id')
    sh_amount_resisual = fields.Float('Residual amount', readonly=True,
                                   compute="_get_amount_residual")
