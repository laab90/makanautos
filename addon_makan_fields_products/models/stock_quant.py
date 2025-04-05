from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    repair_order_id = fields.Many2one('repair.order', string="Orden de Reparación")
    product_id_order = fields.Many2one('product.product', string="Producto a Reparar")
   
