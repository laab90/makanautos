from odoo import models, api, exceptions

class StockPickingCustom(models.Model):
    _inherit = 'stock.picking'

    def write(self, vals):
        """
        Sobreescribimos el método de escritura para bloquear modificaciones en transferencias
        pendientes de validar (estado 'waiting'), y forzar la creación de nuevas transferencias
        si se desea agregar productos adicionales.
        """
        # Verificar si la transferencia está en estado 'waiting' (pendiente de validación)
        if 'state' in vals and vals['state'] == 'waiting':
            # Bloqueamos modificaciones si la transferencia está pendiente de validación
            raise exceptions.UserError('No se pueden modificar las transferencias pendientes de validar. Debes crear una nueva transferencia.')

        # También se puede comprobar si estamos tratando de modificar el destino de la transferencia
        # hacia una ubicación de tránsito y si la transferencia ya está en proceso de validación
        if 'location_dest_id' in vals:
            location_dest = self.env['stock.location'].browse(vals.get('location_dest_id'))
            if location_dest.usage == 'transit':
                for picking in self:
                    if picking.state == 'waiting':
                        raise exceptions.UserError('No se pueden modificar las transferencias hacia ubicaciones de tránsito pendientes de validar.')

        return super(StockPickingCustom, self).write(vals)

    @api.model
    def create(self, vals):
        """
        Sobreescribimos la función de creación de transferencias para asegurarnos de que
        cada transferencia hacia una ubicación de tránsito se maneje de manera independiente.
        """
        location_dest = self.env['stock.location'].browse(vals.get('location_dest_id'))
        
        if location_dest.usage == 'transit':
            # Forzamos que cada nueva transferencia se maneje como independiente
            vals['move_type'] = 'one'  # 'one' significa no agrupar los movimientos

            # Crear la nueva transferencia de manera completamente separada
            picking = super(StockPickingCustom, self).create(vals)
            
            picking.message_post(body="Nueva transferencia creada hacia ubicación de tránsito.")
            return picking
        else:
            # Si no es una ubicación de tránsito, usamos el comportamiento estándar
            return super(StockPickingCustom, self).create(vals)
