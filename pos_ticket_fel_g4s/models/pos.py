# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class PosOrder(models.Model):
    _inherit = "pos.order"

    is_fel = fields.Boolean('FEL', related="account_move.is_fel")
    fel_serie = fields.Char('Serie Fel', related="account_move.serie_fel")
    fel_number = fields.Char('Numero Fel', related="account_move.numero_fel")
    fel_date = fields.Char('Fecha Fel', related="account_move.fel_date")
    fel_uuid = fields.Char('UUID Fel', related="account_move.firma_fel")
    fel_type = fields.Char('Tipo FEL', compute="_compute_fel_type")

    #Customer Data
    customer_vat = fields.Char('Nit', related="partner_id.vat")
    customer_name = fields.Char('Cliente', related="partner_id.name")
    customer_street = fields.Char('Direccion', related="partner_id.street")

    #Company Data
    company_name = fields.Char('Empresa', compute="_compute_company_data")
    company_branch_name = fields.Char('Establecimiento', compute="_compute_company_data")
    company_address = fields.Char('Direccion', compute="_compute_company_data")

    #Contigencia data
    active_contingencia = fields.Boolean('Activar Contigencia', related="account_move.journal_id.active_contingencia")
    no_acceso = fields.Char(string='Numero de Acceso', related="account_move.no_acceso")
    
    @api.depends('account_move.journal_id', 'is_fel')
    def _compute_fel_type(self):
        for rec in self:
            type_name = 'DOCUMENTO TRIBUTARIO ELECTRÓNICO'
            if rec.account_move and rec.account_move.journal_id:
                if rec.account_move.journal_id.tipo_documento_fel == 'FACT':
                    type_name = 'FACTURA'
                if rec.account_move.journal_id.tipo_documento_fel == 'NCRE':
                    type_name = 'NOTA DE CREDITO'
            rec.update({
                'fel_type': type_name,
            })


    @api.depends('company_id', 'account_move.journal_id', 'is_fel')
    def _compute_company_data(self):
        for rec in self:
            company_street = rec.company_id.street
            company_display_name = rec.company_id.name
            company_name = rec.company_id.name
            if rec.account_move and rec.account_move.journal_id:
                if rec.is_fel and rec.account_move.journal_id.direccion:
                    company_street = rec.account_move.journal_id.direccion.street
                    company_display_name = rec.account_move.journal_id.direccion.name
                    company_name = rec.company_id.name
                else:
                    company_street = rec.company_id.street
                    company_name = rec.company_id.name
                    company_display_name = rec.company_id.name
            rec.update({
                'company_address': company_street,
                'company_name': company_name,
                'company_branch_name': company_display_name,
            })

            
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
       

PosOrder()