# -*- coding: utf-8 -*-
from odoo import fields , models,api


class PartnerMapping(models.Model):
	_name = "partner.mapping"
	_inherit = ['woo.comm.channel.mapping']

	type = fields.Selection(
		[
			('contact','Contact'),
			('invoice','Invoice'),
			('delivery','Delivery'),
		],
		default='contact',
		required=1
	)
	store_customer_id = fields.Char('Store Customer ID', required=True)
	odoo_partner_id = fields.Integer('Odoo Partner ID', required=True)
	odoo_partner = fields.Many2one('res.partner', 'Odoo Partner', required=True)
	_sql_constraints = [
		('channel_store_customer_id_uniq',
		'unique(channel_id, store_customer_id,type)',
		'Store partner ID must be unique for channel partner mapping!'),
	]

	@api.onchange('odoo_partner')
	def change_odoo_id(self):
		self.odoo_partner_id = self.odoo_partner.id

	def _compute_name(self):
		for record in self:
			if record.odoo_partner:
				record.name = record.odoo_partner.name
			else:
				record.name = 'Deleted'
