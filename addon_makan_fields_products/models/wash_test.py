from odoo import models, fields

class WashTest(models.Model):
    _name = 'wash.test'
    _description = 'Lavado'

    name = fields.Selection([(str(i), str(i)) for i in range(1, 16)], string="Lavado")
    start_date = fields.Datetime(string="Fecha Inicio")
    end_date = fields.Datetime(string="Fecha Final")
    comments = fields.Text(string="Comentarios")
    repair_order_id = fields.Many2one('repair.order', string="Orden de Reparación")  # Relación con la orden de reparación
