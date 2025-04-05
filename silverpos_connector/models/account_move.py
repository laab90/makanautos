# -*- encoding: UTF-8 -*-
##############################################################################
#
# Copyright (C) 2018-Today J2L Tech GT
# (<https://j2ltechgt.odoo.com>)
#
##############################################################################

from odoo import fields, api, models, tools
import logging

_logger = logging.getLogger( __name__ )

class AccountMove(models.Model):
    _inherit = "account.move"

    silverpos_uuid = fields.Char('UUID')
    silverpos_serie_fel = fields.Char('Serie')
    silverpos_numero_fel = fields.Char('Numero')

    @api.model
    def _action_post_invoice_silverpos(self):
        #company_ids = self.env.company.ids
        #if not company_ids:
        company_ids = self.env['res.company'].sudo().search([]).ids
        invoices_ids = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'draft'), ('company_id', 'in', company_ids)])
        for invoice in invoices_ids:
            try:
                if invoice.state == 'draft':
                    invoice.action_post()
                    invoice.env.cr.commit()
                    log = ("----------------InvoiceId: %s-%s -> Confirmada exitosamente----------------" %(invoice.id, invoice.name))
                    _logger.info(log)
            except Exception as e:
                error = ("InvoiceId: %s-%s -> Error: %s" %(invoice.id, invoice.name, e))
                _logger.info(error)
                invoice.env.cr.rollback()
                pass
AccountMove()

class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    journal_id = fields.Many2one('account.journal', 'Diario', required=False, copy=False)

AccountAnalyticAccount()