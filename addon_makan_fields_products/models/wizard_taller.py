from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class RepairLineWizardNuevo(models.TransientModel):
    _name = 'repair.line.wizard.nuevo'
    _description = 'Nuevo Wizard para seleccionar cotizaciones'

    repair_id = fields.Many2one('repair.order', string='Orden de Reparación', required=True)
    cotizacion_ids = fields.Many2many('repair.order.line.taller', string='Cotizaciones',
                                      domain="[('order_id', '=', repair_id)]")

    from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class RepairLineWizardNuevo(models.TransientModel):
    _name = 'repair.line.wizard.nuevo'
    _description = 'Nuevo Wizard para seleccionar cotizaciones'

    repair_id = fields.Many2one('repair.order', string='Orden de Reparación', required=True)
    cotizacion_ids = fields.Many2many('repair.order.line.taller', string='Cotizaciones',
                                      domain="[('order_id', '=', repair_id)]")

    def generar_reporte(self):
        if not self.repair_id or not self.cotizacion_ids:
            raise ValueError("Faltan cotizaciones o una orden de reparación.")

        # Filtrar las líneas de cotización (sin notas) y las notas
        cotizacion_limpia = self.cotizacion_ids.filtered(lambda l: l.display_type != 'line_note')
        notas_taller = self.cotizacion_ids.filtered(lambda l: l.display_type == 'line_note')

        if not cotizacion_limpia:
            raise ValueError("No hay cotizaciones válidas para generar el reporte.")

        # Leer los datos de las cotizaciones seleccionadas
        repair_line_data = cotizacion_limpia.read(['cotizacion', 'one2manyproduct', 'one2manycantidad'])

        # Leer los datos de las notas de taller y organizarlas por número de cotización
        notas_dict = {}
        for nota in notas_taller:
            # Asociar cada nota con el número de cotización
            notas_dict[nota.cotizacion] = nota.nota_taller

        # Asignar la nota_taller correspondiente a cada línea de cotización si existe
        for line in repair_line_data:
            # Si hay una nota asociada con la misma cotización, se asigna a la línea de cotización
            line['nota_taller'] = notas_dict.get(line['cotizacion'], '')

        _logger.info("Repair ID: %s", self.repair_id.name)
        _logger.info("Cotizaciones seleccionadas: %s", cotizacion_limpia)
        _logger.info("Datos de las líneas de reparación con nota_taller: %s", repair_line_data)

        # Generar el informe basado en el template del nuevo wizard
        return self.env.ref('addon_makan_fields_products.action_report_cotizaciones_taller').report_action(self, data={
            'doc_ids': self.ids,  # Pasar los IDs del wizard
            'doc_model': 'repair.line.wizard.nuevo',  # Nombre del nuevo modelo
            'docs': [self],  # Pasar el objeto actual como lista de un solo objeto
            'repair_line_data': repair_line_data  # Pasar las líneas de reparación
        })


