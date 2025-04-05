# -*- coding: utf-8 -*-
from odoo import fields , models,api


class ShippingMappings(models.Model):
	_name="shipping.mapping"
	_inherit = ['woo.comm.channel.mapping']
	_rec_name = 'shipping_service'

	odoo_carrier_id = fields.Integer('Odoo Carrier ID')
	odoo_shipping_carrier = fields.Many2one('delivery.carrier',string='Odoo Shipping Carrier', required=True)
	shipping_service = fields.Char("Store Shipping Service")
	shipping_service_id = fields.Char("Shipping Serivce ID")
	international_shipping = fields.Boolean('Is International')

	def _compute_name(self):
		for record in self:
			if record.odoo_shipping_carrier:
				record.name = record.odoo_shipping_carrier.name
			else:
				record.name = 'Deleted'

	@api.onchange('odoo_shipping_carrier')
	def change_odoo_id(self):
		self.odoo_carrier_id = self.odoo_shipping_carrier.id
