from odoo import models, fields

class RepairLine(models.Model):
    _inherit = 'repair.fee'

    horas = fields.Float(string="Horas")

    cotizacion = fields.Selection([
        ('1', 'Cotización 1'),
        ('2', 'Cotización 2'),
        ('3', 'Cotización 3'),
        ('4', 'Cotización 4'),
        ('5', 'Cotización 5'),
        ('6', 'Cotización 6'),
        ('7', 'Cotización 7'),
        ('8', 'Cotización 8'),
        ('9', 'Cotización 9'),
        ('10', 'Cotización 10')
    ], string="N° Cotización", tracking=True)

    repair_id = fields.Many2one('repair.order', string='Orden de Reparación')

    statuspiezas = fields.Selection([
        ('1', 'En Cotización'),
        ('2', 'Aprobado'),
        ('3', 'Rechazado por Cliente'),
        ('4', 'Cancelado')
    ], string="Estatus Pieza", tracking=True)
      # Sobrescribimos el método name_get para mostrar el número de cotización
    def name_get(self):
        result = []
        for line in self:
            name = line.cotizacion or 'Sin Cotización'
            result.append((line.id, name))
        return result
