from odoo import models, fields, api
class RepairOrderLine(models.Model):
    _name = 'repair.order.table2.taller'

    order_id_taller2 = fields.Many2one('repair.order', string="Orden de Reparación")
    one2manyproducttaller2 = fields.Char(string="Trabajo")
    one2manycantidadtaller2 = fields.Float(string="Horas")
    display_type = fields.Selection([
        ('line_section', "Sección"),
        ('line_note', "Nota")
    ], default=False, help="Usar para definir la sección de una orden.")

    nota_taller2 = fields.Text(string="Nota Taller")
    
    
  
    
    sequence = fields.Integer(string='Secuencia', default=10)

    _order = 'sequence, id'
  
    @api.model
    def add_note(self):
        self.create({
            'display_type': 'line_note',
            'one2manyproduct': 'Nueva Nota',
            'order_id_taller1': self.env.context.get('default_order_id'),
        })

    # def abrir_nuevo_wizard_cotizaciones(self):
    #     return {
    #         'name': 'Seleccionar Nuevas Cotizaciones',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'repair.line.wizard.nuevo',  # Referencia al nuevo wizard
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_repair_id': self.order_id.id,
    #         },
    #     }
        
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = f"{record.cotizacion or 'Notas'}"
    #         result.append((record.id, name))
    #     return result