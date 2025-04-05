# -*- coding: utf-8 -*-

from odoo import fields , models,api


class PricelistMapping(models.Model):
	_name="pricelist.mapping"
	_order = 'need_sync'
	_rec_name='odoo_pricelist_id'
	_inherit = ['woo.comm.channel.mapping']

	@api.model
	def _needaction_domain_get(self):
		return [('need_sync', '=', 'yes')]

	@api.model
	def store_selectionUsed(self):
		channel_list = []
		channel_list = self.env['woo.comm.channel.sale'].get_channel()
		return channel_list

	name = fields.Char(compute='_compute_name')
	store_currency = fields.Many2one('res.currency', 'Store Currency', required=True)
	store_currency_code = fields.Char('Store Currency Code',
		related='store_currency.name',
		required=True
	)
	odoo_pricelist_id = fields.Many2one('product.pricelist', 'Odoo Pricelist', required=True)
	odoo_currency = fields.Many2one('res.currency',
		related='odoo_pricelist_id.currency_id',
		string='Odoo Currency',
		required=True
	)
	odoo_currency_id = fields.Integer('Odoo Currency ID', required=True)
	channel_id = fields.Many2one('woo.comm.channel.sale', 'Instance', required=True)
	
	@api.onchange('odoo_currency')
	def set_odoo_currency_id(self):
		self.odoo_currency_id = self.odoo_currency.id

	def _compute_name(self):
		for record in self:
			if record.odoo_currency:
				record.name = record.odoo_currency.name
			else:
				record.name = 'Deleted'
