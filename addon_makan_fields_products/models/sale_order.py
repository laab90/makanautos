from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    numorden = fields.Char(string="Número de Orden")

    Ingresadosodr = fields.Boolean(string="Ingresados a ODR")
    algunosIngresadosodr = fields.Boolean(string="Algunos Ingresados a ODR")
    noIngresadosodr = fields.Boolean(string="No Ingresados a ODR")

