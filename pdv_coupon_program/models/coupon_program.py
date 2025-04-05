from odoo import models, fields

class CouponProgram(models.Model):
    _inherit = 'coupon.program'

    pos_config_ids = fields.Many2many(
        'pos.config', string='Punto de Venta',
        help="Restringir las publicaciones a estas tiendas."
    )

    def apply_to_pos(self):
        """
        Esta función actualiza los puntos de venta con el programa de cupones asociado.
        Si no se seleccionan puntos de venta, se aplicará a todos los puntos de venta.
        """
        for program in self:
            if not program.pos_config_ids:
                # Si no hay puntos de venta seleccionados, se aplica a todos los puntos de venta
                pos_configs = self.env['pos.config'].search([])  # Todos los puntos de venta
            else:
                # Si hay puntos de venta seleccionados, solo se aplica a esos
                pos_configs = program.pos_config_ids

            # Asocia el programa de cupones a los puntos de venta correspondientes
            for pos_config in pos_configs:
                cupones_actuales = pos_config.coupon_program_ids.ids
                if program.id not in cupones_actuales:
                    cupones_actuales.append(program.id)
                pos_config.write({'coupon_program_ids': [(6, 0, cupones_actuales)]})

    def write(self, vals):
        """
        Sobrescribe el método write para que al guardar el programa de cupones,
        se aplique automáticamente a los puntos de venta.
        """
        result = super(CouponProgram, self).write(vals)
        self.apply_to_pos()
        return result

    def create(self, vals):
        """
        Sobrescribe el método create para que al crear el programa de cupones,
        se aplique automáticamente a los puntos de venta.
        """
        program = super(CouponProgram, self).create(vals)
        program.apply_to_pos()
        return program
