# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class PosOrder(models.Model):
    _inherit = "pos.order"

    is_fel = fields.Boolean('FEL', related="account_move.is_fel")
    fel_serie = fields.Char('Serie Fel', related="account_move.fel_serie")
    fel_number = fields.Char('Numero Fel', related="account_move.fel_no")
    fel_date = fields.Char('Fecha Fel', related="account_move.fel_date")
    fel_uuid = fields.Char('UUID Fel', related="account_move.uuid")

    #Customer Data
    customer_vat = fields.Char('Nit', related="partner_id.vat")
    customer_name = fields.Char('Cliente', compute="_compute_partner")
    customer_street = fields.Char('Direccion', compute="_compute_partner")

    #Company Data
    company_name = fields.Char('Empresa', compute="_compute_company_data")
    company_branch_name = fields.Char('Establecimiento', compute="_compute_company_data")
    company_address = fields.Char('Direccion', compute="_compute_company_data")

    #Contigencia data
    active_contingencia = fields.Boolean('Activar Contigencia', related="account_move.active_contingencia")
    no_acceso = fields.Char(string='Numero de Acceso', related="account_move.no_acceso")
    
    @api.depends('account_move', 'partner_id')
    def _compute_partner(self):
        for rec in self:
            customer_name = rec.partner_id.name
            customer_address = rec.partner_id.street
            if rec.account_move:
                customer_name = rec.account_move.customer_name
                customer_address = rec.account_move.customer_addres
            rec.update({
                'customer_name': customer_name,
                'customer_street': customer_address,
            })

    @api.depends('account_move')
    def _compute_company_data(self):
        for rec in self:
            company_street = rec.company_id.street
            company_display_name = rec.company_id.nombre_comercial
            company_name = rec.company_id.name
            if rec.account_move:
                if rec.account_move.journal_id.use_street:
                    company_street = rec.account_move.journal_id.establecimiento_street
                    company_display_name = rec.account_move.journal_id.company_name_display
                    company_name = rec.company_id.name
                else:
                    company_street = rec.company_id.street
                    company_name = rec.company_id.name
                    company_display_name = rec.company_id.nombre_comercial
            else:
                company_street = rec.company_id.street
                company_name = rec.company_id.name
                company_display_name = rec.company_id.nombre_comercial
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