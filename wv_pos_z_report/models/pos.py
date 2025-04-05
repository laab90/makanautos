# -*- coding: utf-8 -*-

import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class pos_config(models.Model):
    _inherit = 'pos.config' 

    allow_session_receipt = fields.Boolean('Allow Z Report', default=True)

class ReportSaleDetails(models.AbstractModel):

    _inherit = 'report.point_of_sale.report_saledetails'


    @api.model
    def get_pos_sale_details2(self, date_start=False, date_stop=False, wvconfig_id=False):

        wv_session_id = self.env['pos.session'].search([('config_id','=',wvconfig_id),('state','=','opened')])

        today = fields.Datetime.from_string(fields.Date.context_today(self))
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            # start by default today 00:00:00
            date_start = today

        if date_stop:
            # set time to 23:59:59
            date_stop = fields.Datetime.from_string(date_stop)
        else:
            # stop by default today 23:59:59
            date_stop = today + timedelta(days=1, seconds=-1)

        # avoid a date_stop smaller than date_start
        date_stop = max(date_stop, date_start)

        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)

        orders = self.env['pos.order'].search([
            ('state', 'in', ['paid','invoiced']),
            ('session_id', 'in', wv_session_id.ids)])

        user_currency = self.env.user.company_id.currency_id

        total = 0.0
        products_sold = {}
        taxes = {}
        sales_amount = 0.0
        return_amount = 0.0
        total_with_tax= 0.0
        total_without_tax = 0.0
        total_discount = 0.0
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id.compute(order.amount_total, user_currency)
            else:
                total += order.amount_total
            currency = order.session_id.currency_id

            for line in order.lines:
                key = (line.product_id.pos_categ_id)
                products_sold.setdefault(key, [0.0,0.0])
                products_sold[key][0] += line.qty
                products_sold[key][1] += (line.price_unit*line.qty)-(line.price_unit*line.qty*line.discount/100)
                if line.qty > 0:
                    total_with_tax += line.price_subtotal_incl
                    total_without_tax += line.price_subtotal
                    sales_amount += line.price_subtotal_incl
                    if line.discount > 0:
                        total_discount += ((line.qty * line.price_unit) - line.price_subtotal)
                if line.qty < 0:
                    return_amount += (-line.price_subtotal_incl)

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'total':0.0})
                        taxes[tax['id']]['total'] += tax['amount']
        statement2 = {}
        statement = []
        statements_total = wv_session_id[0].total_payments_amount

        for stm in wv_session_id[0].order_ids.mapped('payment_ids'):
            if (stm.payment_method_id.id,stm.payment_method_id.name) in statement2:
                statement2[(stm.payment_method_id.id,stm.payment_method_id.name)] += stm.amount
            else:
                statement2[(stm.payment_method_id.id,stm.payment_method_id.name)] = stm.amount

        for key in statement2:

            statement.append([key[1],round(statement2[key],3)])

        total_tax = total_with_tax - total_without_tax

        payments = statement

        return {
            'pos_name': wv_session_id[0].config_id.name,
            'cashier_name': wv_session_id[0].user_id.name,
            'opening_balance': wv_session_id[0].cash_register_balance_start,
            'session_start': wv_session_id[0].start_at,
            'session_end': fields.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'sales_amount':round(sales_amount,2),
            'return_amount':round(return_amount,2),
            'total_with_tax':round(total_with_tax,2),
            'total_without_tax':round(total_without_tax,2),
            'total_tax':round(total_tax,2),
            'total_discount':round(total_discount,2),
            'total_paid':round(total,2),
            'payments': payments,
            'company_name': self.env.user.company_id.name,
            'taxes': list(taxes.values()),
            'categs': sorted([{
                'categ_id': categ_id.id,
                'categ_name': categ_id.name,
                'amount': lis[1],
                'quantity': lis[0]
            } for (categ_id), lis in products_sold.items()], key=lambda l: l['categ_name'])
        }

