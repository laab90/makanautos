# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class AccountBenefPayment(models.Model):
    _inherit = "account.payment"

    activa_benef = fields.Boolean(string='¿Usar Beneficiario?', readonly=False, help="Marque si emite cheque y necesita usar beneficiario")
    beneficiario = fields.Char(string='Beneficiario', required=False, readonly=False, states={'posted':[('readonly',True)]})
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user) #para imprimir responsable de elaborar cheque [[user_id.login]]
    type_checkp = fields.Selection([
    			('NGO' , 'NEGOCIABLE'),
    			('NONGO' , 'NO NEGOCIABLE')], 'Tipo de Cheque', required=False, readonly=False,)



