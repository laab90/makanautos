# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class ExportOdooProducts(models.TransientModel):
	_inherit = ['export.products']
	_name = "export.odoo.products"

	def export_odoo_products(self):
		if hasattr(self, 'export_%s_products' % self.channel_id.channel):
			return getattr(self, 'export_%s_products' % self.channel_id.channel)()


	def update_odoo_products(self):
		if hasattr(self, 'update_%s_products' % self.channel_id.channel):
			return getattr(self, 'update_%s_products' % self.channel_id.channel)()
