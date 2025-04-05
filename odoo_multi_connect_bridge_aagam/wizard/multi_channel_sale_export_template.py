# -*- coding: utf-8 -*-

from odoo import api,models,fields
import logging
_logger = logging.getLogger(__name__)

class ExportTemplates(models.TransientModel):
    _inherit = 'export.templates'

    def submit(self):
        message=''
        if self.operation == 'export':
            message = self.channel_id.action_export_woo_comm_product()
        else:
            message = self.channel_id.action_woo_comm_updated_product()
        return message
