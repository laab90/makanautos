from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    repair_order_id = fields.Many2one('repair.order', string="Orden de Reparación")
    product_id_order = fields.Many2one('product.product', string="Producto a Reparar")

    @api.onchange('repair_order_id')
    def _onchange_repair_order_id(self):
        if self.repair_order_id:
            # Si el producto es de tipo product.template, necesitamos obtener el product_variant_id
            self.product_id_order = self.repair_order_id.product_id.product_variant_id
        else:
            self.product_id_order = False