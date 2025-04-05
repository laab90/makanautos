# -*- coding: utf-8 -*-
from odoo import fields ,models, api, _


class SyncChannel(models.Model):
	_name="sync.channel"
	_inherit = ['woo.comm.channel.mapping']
	_rec_name="action_on"


	status = fields.Selection([('error','Error'), ('success','Success')],
		string='Status', required=True)
	action_on =  fields.Selection([('variant','Variant'),
					 ('template','Template'),
					 ('product','Product'),
					 ('category','Category'),
					 ('order','Order'),
					 ('customer','Customer'),
					 ('shipping','Shipping'),
					 ('attribute','Attribute'),
					 ('attribute_value','Attribute Value')],
		string='Action On', required=True
	)
	action_type = fields.Selection([('import', 'Import'), ('export', 'Export')],
		string='Action Type')
	ecomstore_refrence = fields.Char('Store ID')
	odoo_id = fields.Text('Odoo ID')
	summary = fields.Text('Summary',required=True)

	@api.model
	def cron_clear_history(self):
		for rec in self.search([('status','=','success')]):
			rec.unlink()
