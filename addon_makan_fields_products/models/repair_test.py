from odoo import models, fields

class RepairTest(models.Model):
    _name = 'repair.test'
    _description = 'Repair Test'

    name = fields.Selection([(str(i), str(i)) for i in range(1, 16)], string="Prueba")
    start_date = fields.Datetime(string="Fecha Inicio")
    end_date = fields.Datetime(string="Fecha Final")
    comments = fields.Text(string="Comentarios")
    repair_order_id = fields.Many2one('repair.order', string="Orden de Reparación")