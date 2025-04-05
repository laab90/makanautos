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
                    'amount': i.amount,
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
                'product_id': line.product_id.name,
                'qty': line.qty,
                'price_unit': line.price_unit,
                'unit_name':line.product_id.uom_id.name,
                'discount': line.discount,
                })
        order = {
        	'name':pos_order.pos_reference,
        	'amount_total':pos_order.amount_total,
        	'amount_tax':pos_order.amount_tax,
        }
        return {
        	'order_line':order_line,
        	'payment_lines':payment_lines,
        	'discount':discount,
        	'change':change,
        	'order':order
        	}




    