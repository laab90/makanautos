# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
	_inherit = "pos.order"
	
	txt_filename = fields.Char('Archivo', related="account_move.txt_filename")
	file = fields.Binary('Archivo', related="account_move.file")
	
	@api.model
	def get_fel(self, order):
		_logger.info('***********************order_id*************************')
		_logger.info(order)
		move_id = self.env['account.move'].search([('id', '=', int(order['move_id']))])
		_logger.info('***********************order_id2*************************')
		_logger.info(move_id)
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		return {
			'type': 'ir.actions.act_url',
			'name': 'Factura Electroncia',
			'url': base_url + "/web/content/?model=" + "account.move" +"&id=" + str(move_id.id) + "&filename_field=file_name&field=file&download=true&filename=" + str(move_id.txt_filename),
			'target': 'self',
		}
	

	def _generate_pos_order_invoice(self):
		moves = self.env['account.move']
		for order in self:
			# Force company for all SUPERUSER_ID action
			if order.account_move:
				moves += order.account_move
				continue
			if not order.partner_id:
				raise UserError(_('Please provide a partner for the sale.'))

			move_vals = order._prepare_invoice_vals()
			new_move = order._create_invoice(move_vals)

			order.write({'account_move': new_move.id, 'state': 'invoiced'})
			new_move.sudo().with_company(order.company_id).action_post()
			moves += new_move
			order._apply_invoice_payments()

		if not moves:
			return {}

		return {
			'name': _('Customer Invoice'),
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'context': "{'move_type':'out_invoice'}",
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			'res_id': moves and moves.ids[0] or False,
		}



PosOrder()