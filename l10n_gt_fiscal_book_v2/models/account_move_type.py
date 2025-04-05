# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountMoveType(models.Model):
    _name = "account.move.type.tr"
    _description = "Account Move Type"

    name = fields.Char('Description', required=True, copy=False)
    code = fields.Char('Code', required=True, copy=False)
    type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase')], string="Type", default="sale")

    #Multicompany
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)

AccountMoveType()