from odoo import models, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'

    user_id = fields.Many2one('res.users', string='Cashier')

    # Permitir que el campo user_id sea modificado desde el backend
    def write(self, values):
        if 'user_id' in values:
            # Aquí puedes agregar cualquier validación adicional si es necesario
            pass
        return super(PosOrder, self).write(values)
