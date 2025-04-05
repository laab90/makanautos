# -*- coding: utf-8 -*-
from odoo import fields , models, api, _

class WooCommChannelMappings(models.Model):
	_name = "woo.comm.channel.mapping"
	_order = 'need_sync'


	@api.model
	def _get_channel_domain(self):
		return [('state', '=', 'validate')]

	@api.model
	def selection_data(self):
		list_data = []
		list_data = self.env['woo.comm.channel.sale'].get_channel()
		return list_data

	name = fields.Char(compute='_compute_name')
	channel_id = fields.Many2one('woo.comm.channel.sale', 'Instance', required=True, domain=_get_channel_domain)
	store_selection = fields.Selection(selection='selection_data', string="Channel")
	store_id = fields.Char('WooCommerce Store ID')
	need_sync = fields.Selection(
		[('yes','Yes'),('no','No')],
		string='Update Required',
		default='no',
		required=True
	)
	operation = fields.Selection(
		[('import', 'Import'), ('export', 'Export')],
		string="Operation",
		default="import",
		required=True
		)

	def _compute_name(self):
		pass

	@api.model
	def get_need_sync_mapping(self, domain):
		domain = domain and []
		map_domain = domain + [
			('need_sync', 'in', ['yes']),
		]
		return self.search(map_domain)
