import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class RepairLineWizard(models.TransientModel):
    _name = 'repair.line.wizard'
    _description = 'Wizard para seleccionar cotizaciones'

    repair_id = fields.Many2one('repair.order', string='Orden de Reparación', required=True)
    cotizacion_ids = fields.Many2many('repair.line', string='Cotizaciones',
                                      domain="[('repair_id', '=', repair_id)]")
    cotizacion_ids_mano_obra = fields.Many2many(
    'repair.fee',  # Ahora apunta a repair.fee
    string='Cotizaciones',
    domain="[('repair_id', '=', repair_id)]"  # Filtra por repair_id
)

    def generar_reporte(self):
        if not self.repair_id or not self.cotizacion_ids:
            raise ValueError("Faltan cotizaciones o una orden de reparación.")

        repair_line_data = self.cotizacion_ids.read(['cotizacion', 'name', 'precio_temporal', 'statuspiezas'])

        _logger.info("Repair ID: %s", self.repair_id.name)
        _logger.info("Cotizaciones IDs: %s", self.cotizacion_ids)
        _logger.info("Datos de las líneas de reparación: %s", repair_line_data)

        # Asegúrate de pasar el contexto correcto para doc
        return self.env.ref('addon_makan_fields_products.action_report_cotizaciones').report_action(self, data={
            'doc_ids': self.ids,  # Pasar los IDs del wizard
            'doc_model': 'repair.line.wizard',  # Nombre del modelo
            'docs': [self],  # Pasar el objeto actual como lista de un solo objeto
            'repair_line_data': repair_line_data  # Pasar las líneas de reparación
        })
    

    def generar_reporte_manoobra(self):
        if not self.repair_id:
            raise ValueError("Falta seleccionar una orden de reparación.")
        if not self.cotizacion_ids_mano_obra:
            raise ValueError("Faltan cotizaciones seleccionadas.")

        # Leer los datos directamente de los registros seleccionados
        repair_fee_data = self.cotizacion_ids_mano_obra.read(['cotizacion', 'name', 'price_unit','horas'])

        _logger.info("Generando reporte M.O: Reparación ID: %s, Repair Fees: %s", self.repair_id.name, repair_fee_data)

        # Generar el reporte con los datos obtenidos
        return self.env.ref('addon_makan_fields_products.action_report_cotizaciones_manoobra').report_action(self, data={
            'doc_ids': self.ids,
            'doc_model': 'repair.line.wizard',
            'docs': [self],
            'repair_line_data': repair_fee_data,  # Cambiar a repair_line_data para que coincida con la plantilla
            'chasis': self.repair_id.chasis,  # Agrega el campo chasis aquí
           'propietario': self.repair_id.propietario.name  # Campo propietario (nombre)
        })
        