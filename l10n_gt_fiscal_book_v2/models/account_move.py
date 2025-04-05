# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = "account.move"
    
    #@api.model
    #def _default_type(self):
    #    return self.env.ref("treming_gt_fiscal_book.type_local") or False

    gt_move_type_tr_id = fields.Many2one('account.move.type.tr', 'Move Type', required=False, copy=False, tracking=True)

    gt_document_type_tr = fields.Selection([
		('FC', 'Factura Cambiaria'),
		('FE', 'Factura Especial'),
		('FCE', 'Factura Electronica'),
		('NC', 'Nota de Credito'),
		('ND', 'Nota de Debito'),
		('FPC', 'Factura Peq. Contribuyente'),
		('DA', 'Declaracion Unica Aduanera'),
		('FA', 'FAUCA'),
		('FO', 'Formulario SAT'),
		('ONAF', 'Otros No Afectos'),
		('EP', 'Escritura Publica')],'Document Type', default='FC', required=False)

AccountMove()

