# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    factura_cambiaria = fields.Boolean('Factura Cambiaria')
    is_fel = fields.Boolean('¿Activar FEL?', required=False, default=False)
    codigo_est = fields.Char(string='Codigo Establecimiento', help='Número del establecimiento donde se emite el documento. Es el que aparece asignado por SAT en sus registros.')
    use_street = fields.Boolean('¿Usar otra direccion?', default=False)
    establecimiento_street = fields.Text('Direccion de establecimiento', required=False)
    company_name_display = fields.Char('Nombre Comercial', required=False)

    #Contigencia
    

AccountJournal()