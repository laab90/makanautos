# -*- coding: utf-8 -*-
from odoo import fields , models,api

class WooCommAccountMapping(models.Model):
	_name = "woo.comm.account.mapping"
	_inherit = ['woo.comm.channel.mapping']

	tax_type = fields.Selection([('fixed', 'Fixed'), ('percent', 'Percentage')],
								string="Tax Types", default='percent', required=True)
	tax_id = fields.Integer('Tax ID', required=True)
	account_tax_id = fields.Many2one('account.tax', 'Tax Name', required=True)
	is_tax_include_in_price = fields.Boolean("Is Tax Include in price? ")
	wc_tax_id =  fields.Char('Woo-commerce Tax',required=True)

	def _compute_name(self):
		for record in self:
			if record.tax_name:
				record.name = record.tax_name.name
			else:
				record.name = 'Deleted'

	@api.onchange('account_tax_id')
	def onchange_account_tax_id(self):
		for record in self:
			record.account_tax_id = record.account_tax_id.id

class WooCommJournalMapping(models.Model):
	_name="woo.comm.journal.mapping"
	_inherit = ['woo.comm.channel.mapping']

	wc_journal_name =  fields.Char('Woo-Commerce Payment Method',required=True)
	journal_code =  fields.Char('Journal Code',required=True, related="journal_id.code")
	ref_odoo_journal_id = fields.Integer('Reference Odoo Journal ID',required=True)
	journal_id = fields.Many2one('account.journal',string='Journal Name', required=True)

	def _compute_name(self):
		for record in self:
			if record.journal_id and record.journal_id.name:
				record.name = record.journal_id.name
			else:
				record.name = 'Deleted'

	@api.onchange('journal_id')
	def onchange_journal_id(self):
		for record in self:
			record.ref_odoo_journal_id = record.journal_id.id
