# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class WizardMessage(models.TransientModel):
	_name = "wizard.message"
	
	text = fields.Text('Message')

class UpdateMappingWizard(models.TransientModel):
	_name='update.mapping.wizard'

	need_sync = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Update Required', default='yes', required=True)

	def save_status(self):
		for recrod in self:
			context = dict(recrod._context)
			model  =  self.env[context.get('active_model')]
			active_ids = model.browse(context.get('active_ids'))
			for active_id in active_ids:
				active_id.need_sync =recrod.need_sync
