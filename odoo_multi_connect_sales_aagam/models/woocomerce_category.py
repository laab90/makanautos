# -*- coding: utf-8 -*-
from odoo import fields ,models, api, _

class WooCommerceProductCategoryMapping(models.Model):
	_name = "woo.comm.product.category.mapping"
	_inherit = ['woo.comm.channel.mapping']
	_rec_name = "product_category_id"

	wc_product_categ_id = fields.Char('WooCommerce Category ID', required=True)
	categ_id = fields.Integer('Product Category ID', required=True)
	product_category_id = fields.Many2one('product.category', 'Product Category')
	is_leaf_category = fields.Boolean('Is Leaf Category? ')

	_sql_constraints = [
		('channel_store_wc_product_categ_id_uniq',
		'UNIQUE(channel_id, wc_product_categ_id)',
		'Store category ID must be unique for channel category mapping!'),
		('channel_categ_id_uniq',
		'UNIQUE(channel_id, categ_id)',
		'Odoo category ID must be unique for channel category mapping!'),
	]

	@api.onchange('product_category_id')
	def onchange_product_category_id(self):
		for record in self:
			record.categ_id = record.product_category_id.id

	def unlink(self):
		for record in self:
			if record.wc_product_categ_id:
				match = record.channel_id.match_category_feeds(record.wc_product_categ_id)
				if match: match.unlink()
		return super(WooCommerceProductCategoryMapping, self).unlink()

	def _compute_name(self):
		for record in self:
			if record.category_name:
				record.name = record.category_name.name
			else:
				record.name = 'Deleted'
