# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = "res.company"
    
    requestor_fel = fields.Char('Requestor FEL', copy=False)
    usuario_fel = fields.Char('Usuario FEL', copy=False)
    pruebas_fel = fields.Boolean('Modo de Pruebas FEL')
    afiliacion_iva_fel = fields.Selection([('GEN', 'GEN'), ('PEQ', 'PEQ'), ('EXE', 'EXE')], 'Afiliación IVA FEL', default='GEN')
    frases_fel = fields.Text('Frases FEL')
    frase_ids = fields.Many2many('satdte.frases', 'company_frases_rel', 'company_id', 'frases_id', 'Frases')
    fel_currency_id = fields.Many2one('res.currency', 'FEL Moneda', required=False, copy=False)
