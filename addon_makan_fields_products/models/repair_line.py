from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class RepairLine(models.Model):
    _inherit = 'repair.line'
    
    tipo_proveedor = fields.Selection([
        ('nacional', 'Proveedor Nacional'),
        ('extranjero', 'Proveedor Extranjero')
    ], string="Tipo de Proveedor", tracking=True)

    precio_temporal = fields.Float(string="Precio Temporal", tracking=True)

    @api.onchange('precio_temporal', 'tipo_proveedor')
    def _onchange_precio_temporal(self):
        for record in self:
            if record.tipo_proveedor == 'nacional':
                record.price_unit = record.precio_temporal * 1.45
            elif record.tipo_proveedor == 'extranjero':
                record.price_unit = record.precio_temporal * 22
            else:
                record.price_unit = 0


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

    statuspiezas = fields.Selection([
        ('1', 'En Cotización'),
        ('2', 'Aprobado'),
        ('3', 'Rechazado por Cliente'),
        ('4', 'Cancelado')
    ], string="Estatus Pieza", tracking=True)
    order_id = fields.Many2one('repair.order', string="Orden de Reparación")
    def write(self, vals):
        # Guardamos el valor anterior antes de la actualización
        for record in self:
            old_status = record.statuspiezas

        # Llamamos al método original para escribir los cambios
        res = super(RepairLine, self).write(vals)

        # Diccionario para mapear los valores de statuspiezas a su descripción textual
        status_mapping = {
            '1': "En Cotización",
            '2': "Aprobado",
            '3': "Rechazado por Cliente",
            '4': "Cancelado"
        }

        # Verificamos si el campo 'statuspiezas' ha cambiado
        for record in self:
            if 'statuspiezas' in vals and record.statuspiezas != old_status:
                # Publicamos un mensaje en el chatter del repair.order asociado
                repair_order = record.repair_id
                if repair_order:
                    old_status_name = status_mapping.get(old_status, "Desconocido")
                    new_status_name = status_mapping.get(record.statuspiezas, "Desconocido")
                    repair_order.message_post(
                        body=f"El Estatus del Producto '{record.name}' de la Cotización {record.cotizacion} ha cambiado de {old_status_name} a {new_status_name}"
                    )

        return res
    

    # Sobrescribimos el método name_get para mostrar el número de cotización
    def name_get(self):
        result = []
        for line in self:
            name = line.cotizacion or 'Sin Cotización'
            result.append((line.id, name))
        return result

   
    
