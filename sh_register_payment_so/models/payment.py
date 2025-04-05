# -*- coding: utf-8 -*-

from odoo import api,models, fields

class AccountPayment(models.Model):
	""" Inherited Account Payment to add sale_id field """
	_inherit = "account.payment"
	
	sale_id = fields.Many2one('sale.order')
