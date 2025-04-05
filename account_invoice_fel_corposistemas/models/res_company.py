# -*- coding: utf-8 -*-

from odoo import fields, models
import requests
import json
import dateutil.parser
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'

    regimen_iva = fields.Char(string='Regimen asociado de IVA', help='Regimen asociado de IVA en Guatemala. Iniciales necearias para comunicacion con FEL. En caso de duda, referirse a documentacion oficial de la Superintendencia de Administracion Tributaria.')
    codigo_est = fields.Char(string='Codigo Establecimiento', help='Número del establecimiento donde se emite el documento. Es el que aparece asignado por SAT en sus registros.')
    nombre_est = fields.Char(string='Nombre de Establecimiento', help='Nombre o abreviatura Número del establecimiento donde se emite el documento. Es el que aparece asignado por SAT en sus registros.')
    nombre_comercial = fields.Char(string='Nombre Comercial', help='Indica el nombre comercial del establecimiento (de acuerdo a los registros tributarios) donde se emite el documento.')
    request_id = fields.Char('IDRequest')
    frase_ids = fields.Many2many('satdte.frases', 'company_frases_rel', 'company_id', 'frases_id', 'Frases')
    export_code = fields.Char('Codigo Exportador', required=False, copy=False)
    #URL Corposistemas
    url_request = fields.Text('Url Requests')
    url_nit = fields.Text('Url Nit')


ResCompany()