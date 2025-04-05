from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'account.move'

    serie_fel_marvin = fields.Char( string="Serie Fel")
    numero_fel_marvin = fields.Char(string="Numero Fel")
   
  