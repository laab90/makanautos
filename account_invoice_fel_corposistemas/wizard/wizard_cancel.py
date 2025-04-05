# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
import datetime

import logging

_logger = logging.getLogger( __name__ )

class WizardFELCancel(models.TransientModel):
    _name = 'wizard.fel.cancel'
    _description = 'Wizard to cancel invoice in FEL'
    
    invoice_id = fields.Many2one('account.move', 'Documento', required=False)
    notes = fields.Text('Motivo de anulacion', required=False)

    def action_cancel(self):
        xml = ""
        for rec in self:
            if rec.invoice_id:
                rec.invoice_id.write({'narration': rec.notes})
                xml = rec.invoice_id.generate_xml_cancel()
                _logger.info('************************XML generate_xml_cancel***************************')
                _logger.info(xml)
                xml_post = rec.invoice_id.generate_xml_dte(xml, transaction="SYSTEM_REQUEST", type="VOID_DOCUMENT")
                #raise UserError(('%s') %(xml_post.decode('utf-8')))
                _logger.info('************************XML Anulacion***************************')
                _logger.info(xml_post)
                rec.invoice_id.post_cancel_dte(xml_post.decode('utf-8'))
                rec.invoice_id.button_draft()
                rec.invoice_id.button_cancel()
        return True

WizardFELCancel()