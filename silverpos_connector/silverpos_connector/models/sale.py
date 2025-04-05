# -*- encoding: UTF-8 -*-
##############################################################################
#
# Copyright (C) 2018-Today J2L Tech GT
# (<https://j2ltechgt.odoo.com>)
#
##############################################################################

from odoo import fields, api, models, tools
from datetime import datetime

import logging

_logger = logging.getLogger( __name__ )

class SaleOrder(models.Model):
    _inherit = "sale.order"

    silverpos_id = fields.Integer('IdSilverPos', required=False, )
    silverpos_uuid = fields.Char('UUID')
    silverpos_serie_fel = fields.Char('Serie')
    silverpos_numero_fel = fields.Char('Numero')
    silverpos_user_id = fields.Many2one('res.users', 'Usuario SilverPos', required=False, copy=False)
    silverpos_order_date = fields.Date('Fecha', compute="_compute_order_date")
    journal_id = fields.Many2one('account.journal', 'Diario', related="analytic_account_id.journal_id")


    @api.depends('date_order')
    def _compute_order_date(self):
        for rec in self:
            date = False
            if rec.date_order:
                date = rec.date_order.date()
            rec.update({
                'silverpos_order_date': date,
            })

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        for rec in self:
            res.update({
                'silverpos_uuid': rec.silverpos_uuid,
                'silverpos_serie_fel': rec.silverpos_serie_fel,
                'silverpos_numero_fel': rec.silverpos_numero_fel,
                'invoice_user_id': rec.silverpos_user_id.id or rec.user_id.id,
                'invoice_date': datetime.strptime(str(rec.date_order), "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d'),
            })
            if rec.journal_id:
                res.update({
                    'journal_id': rec.journal_id.id or False,
                })
        return res
    
    @api.model
    def _action_confirm_orders(self):
        count = 0
        item = 0
        so_obj = self.env['sale.order']
        #company_ids = self.env.company.ids
        #if not company_ids:
        company_ids = self.env['res.company'].sudo().search([]).ids
        orders_ids = self.env['sale.order'].sudo().search([('silverpos_id', '!=', 0), ('state', '=', 'draft'), ('company_id', 'in', company_ids)])
        for order in orders_ids:
            try:
                item += 1
                #if order.state == 'draft':
                order.sudo().action_confirm()
                count += 1
                so_obj += order
                if count == 20:
                    self.env.cr.commit()
                    log = ("----------------Item %s OrderIds: %s-%s -> Transacciones Liberadas----------------" %(item, order.id, order.name))
                    _logger.info(log)
                    so_obj = self.env['sale.order']
                    count = 0
                #order.env.cr.commit()
                #_logger.info(("SO Confirmada con Exito..! -> %s" %(order.name)))
                log = ("----------------Item %s OrderId: %s-%s -> Confirmada exitosamente----------------" %(item, order.id, order.name))
                _logger.info(log)
            except Exception as e:
                error = ("%s %s -> %s" %(order.id, order.name, e))
                _logger.info(error)
                #order.env.cr.rollback()
                pass
        if so_obj and len(so_obj.ids) > 0:
            self.env.cr.commit()
        return True

    @api.model
    def _action_invoiced_orders(self):
        #company_ids = self.env.company.ids
        #if not company_ids:
        company_ids = self.env['res.company'].sudo().search([]).ids
        orders_ids = self.env['sale.order'].sudo().search([('silverpos_id', '!=', 0), ('state', '=', 'sale'), ('invoice_status', '=', 'to invoice'), ('company_id', 'in', company_ids)])
        for order in orders_ids:
            try:
                if order.state == 'sale':
                    order.sudo()._create_invoices()
                    order.env.cr.commit()
            except Exception as e:
                error = ("%s %s -> %s" %(order.id, order.name, e))
                _logger.info(error)
                order.env.cr.rollback()
                pass


SaleOrder()

class AccountPayment(models.Model):
    _inherit = 'account.payment'


    @api.model
    def _action_post_payment_silverpos(self, records=100):
        #company_ids = self.env.user.company_ids.ids
        #if not company_ids:
        company_ids = self.env['res.company'].sudo().search([]).ids
        payments_ids = self.env['account.payment'].search([('sale_id', '!=', False), ('state', '=', 'draft'), ('company_id', 'in', company_ids)], limit=records)
        for payment in payments_ids:
            try:
                if payment.state == 'draft':
                    payment.action_post()
                    if payment.sale_id and payment.sale_id.invoice_ids:
                        domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
                        #payment.write({
                        #    'invoice_ids': payment.sale_id.invoice_ids.ids if payment.sale_id.invoice_ids else False,
                        #})
                        payment_lines = payment.line_ids.filtered_domain(domain)
                        invoice_lines = payment.sale_id.invoice_ids.line_ids.filtered_domain(domain)
                        for account in payment_lines.account_id:
                            (payment_lines + invoice_lines).filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
                    #payment.post()
                    payment.env.cr.commit()
                    log = ("----------------PaymentId: %s-%s -> Asentado exitosamente----------------" %(payment.id, payment.name))
                    _logger.info(log)
            except Exception as e:
                error = ("PaymentId: %s -> Error: %s" %(payment.id, e))
                _logger.info(error)
                payment.env.cr.rollback()
                pass
AccountPayment()

class StockMove(models.Model):
    _inherit = "stock.move"



    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = False
            if self.sale_line_id.order_id.silverpos_order_date:
                date = self.sale_line_id.order_id.silverpos_order_date
            else:
                date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'type': 'entry',
            })
            new_account_move.post()
StockMove()