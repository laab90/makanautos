# -*- coding: utf-8 -*-


from odoo import fields, models,tools,api, _
from functools import partial
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class pos_config(models.Model):
    _inherit = 'pos.config' 
    
    pos_order_reprint = fields.Boolean("Allow Order Reprint",default=True)


    @api.model
    def get_order_detail(self, order_id):
        pos_order = self.env['pos.order'].browse(order_id)
        payment_lines = []
        change = 0
        for i in pos_order.payment_ids:
            if i.amount > 0:
                temp = {
                    'id': i.id,
                    'amount':  "{0:.2f}".format(i.amount),
                    'name': i.payment_method_id.name
                }
                payment_lines.append(temp)
            else:
                change += i.amount
        discount = 0
        order_line = []    
        for line in pos_order.lines:
            discount += (line.price_unit * line.qty * line.discount) / 100
            order_line.append({
                'id': line.id,
                'product_id': line.product_id.name,
                'qty': line.qty,
                'price_unit': "{0:.2f}".format(line.price_unit),
                'unit_name':line.product_id.uom_id.name,
                'discount': line.discount,
                'price_subtotal': "{0:.2f}".format(line.price_subtotal_incl),
                })
        order = {
        	'name':pos_order.pos_reference,
        	'amount_total': "{0:.2f}".format(pos_order.amount_total),
        	'amount_tax': "{0:.2f}".format(pos_order.amount_tax),
        }
        invoice = {}
        if pos_order and pos_order.account_move:
            invoice = {
                'customer_name': pos_order.customer_name,
                'customer_street': pos_order.customer_street,
                'customer_vat': pos_order.customer_vat,
                'company_name': pos_order.company_name,
                'company_branch_name': pos_order.company_branch_name,
                'company_address': pos_order.company_address,
                'is_fel': pos_order.is_fel,
                'invoice_number': pos_order.account_move.name if pos_order.account_move else '',
                'fel_serie': pos_order.fel_serie,
                'fel_number': pos_order.fel_number,
                'fel_date': pos_order.fel_date,
                'fel_uuid': pos_order.fel_uuid,
                'is_contingencia': 'TRUE' if pos_order.active_contingencia else 'FALSE',
                'no_acceso': pos_order.no_acceso,
            }
        return {
        	'order_line':order_line,
        	'payment_lines':payment_lines,
            'total_tax': "{0:.2f}".format(pos_order.amount_tax),
            'total_with_tax': "{0:.2f}".format(pos_order.amount_total),
        	'discount': "{0:.2f}".format(discount),
        	'change': "{0:.2f}".format(change),
        	'order':order,
            'invoice': invoice
        	}




    