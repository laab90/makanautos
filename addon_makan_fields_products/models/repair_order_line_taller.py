from odoo import models, fields, api
class RepairOrderLine(models.Model):
    _name = 'repair.order.line.taller'

    order_id = fields.Many2one('repair.order', string="Orden de Reparación")
    one2manyproduct = fields.Char(string="Item Taller")
    one2manycantidad = fields.Float(string="Cantidad")
    display_type = fields.Selection([
        ('line_section', "Sección"),
        ('line_note', "Nota")
    ], default=False, help="Usar para definir la sección de una orden.")

    nota_taller = fields.Text(string="Nota Taller")
    
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
    
    statuslineataller = fields.Selection([
            ('1', 'Solicitado'),
            ('2', 'No Autorizado'),
            ('3', 'Recibido'),
            ('4', 'Importación'),
            ('5', 'Proveedor N')
           
        ], string="Estatus Linea", tracking=True)
    
    sequence = fields.Integer(string='Secuencia', default=10)

    _order = 'sequence, id'
  
    @api.model
    def add_note(self):
        self.create({
            'display_type': 'line_note',
            'one2manyproduct': 'Nueva Nota',
            'order_id': self.env.context.get('default_order_id'),
        })

    def abrir_nuevo_wizard_cotizaciones(self):
        return {
            'name': 'Seleccionar Nuevas Cotizaciones',
            'type': 'ir.actions.act_window',
            'res_model': 'repair.line.wizard.nuevo',  # Referencia al nuevo wizard
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_repair_id': self.order_id.id,
            },
        }
        
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.cotizacion or 'Notas'}"
            result.append((record.id, name))
        return result