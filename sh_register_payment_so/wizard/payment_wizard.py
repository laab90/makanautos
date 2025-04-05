# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp


class AdvancePaymentWizard(models.TransientModel):

    _name = "account.payment.wizard"

    """ Defined Fields"""
    sh_origin = fields.Char(string="Origen",readonly=True)
    sh_payment_amount = fields.Float("Monto de pago",digits=dp.get_precision('Product Price'))
    sh_total_amount = fields.Float("Total", readonly=True)
    sh_date = fields.Date("Fecha", required=True,default=fields.Date.context_today)
    sh_currency_rate = fields.Float("Tasa de cambio", digits=(16, 6), default=1.0,readonly=True)
    sh_currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)

    """ Method to get default journal_id populate"""
    @api.model
    def _default_journal_id(self):
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1)

    sh_journal_id = fields.Many2one('account.journal', string="Metodo de pago", required=True,default=_default_journal_id)

    """ Method to get default payment_id populate"""
    @api.model
    def _default_payment_id(self):
        return self.env['account.payment.method'].search([], limit=1)

    sh_payment_method_id = fields.Many2one('account.payment.method', string="Tipo de pago",default=_default_payment_id)
   

    """ Method to validate advance payment amount"""
    @api.constrains('sh_payment_amount')
    def validate_advance_amount(self):
        if self.sh_payment_amount <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be "
                                               "positive."))
        if self.env.context.get('active_id', False):
            order = self.env["sale.order"].\
                browse(self.env.context['active_id'])
            if self.sh_payment_amount > order.sh_amount_resisual:
                raise exceptions.ValidationError(_("Amount of advance is "
                                                   "greater than residual "
                                                   "amount on sale"))

    """ Method to auto populate some of the values in payment wizard """
    @api.model
    def default_get(self, fields):
        rec = super(AdvancePaymentWizard, self).default_get(fields)
        active_id= self._context.get('active_id')
        active_model = self._context.get('active_model')
        sale_order = self.env[active_model].browse(active_id)
        if not rec.get('sh_origin') and (not fields or 'sh_origin' in fields):
            rec['sh_origin'] = sale_order.name
            rec['sh_total_amount'] = sale_order.amount_total
            rec['sh_currency_id'] = sale_order.pricelist_id.currency_id.id
            #rec['sh_currency_rate'] = self.env['res.currency']._get_conversion_rate(sale_order.company_id.currency_id, sale_order.currency_id)
        return rec

    """ Method to Post payment data to account.payment object """
    def make_advance_payment(self):
        sale_order = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        partner_id = sale_order.partner_id.id
        date = self[0].sh_date
        company = sale_order.company_id

        """ Preparing payment values to create record in account.payment object """
        payment_values = {'payment_type': 'inbound',
                       'partner_id': partner_id,
                       'partner_type': 'customer',
                       'journal_id': self[0].sh_journal_id.id,
                       'company_id': company.id,
                       'currency_id':sale_order.pricelist_id.currency_id.id,
                       'payment_date': date,
                       'amount': self[0].sh_payment_amount,
                       'sale_id': sale_order.id,
                       'invoice_ids': sale_order.invoice_ids.ids if sale_order.invoice_ids else False,
                       'communication': self[0].sh_origin or sale_order.name,
                       'payment_method_id': self.sh_payment_method_id.id
                       }
        payment = self.env['account.payment'].create(payment_values)
        payment.post()
        