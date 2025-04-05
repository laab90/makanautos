from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    marca = fields.Char(string="Marca")
    modelo = fields.Char(string="Modelo")
    kilometraje = fields.Float(string="Kilometraje")
    chasis = fields.Char(string="Chasis")
    placa = fields.Char(string="Placa")
    motor = fields.Char(string="Motor")
    anio = fields.Integer(string="Año")
    color = fields.Char(string="Color")
    cilindraje = fields.Char(string="Cilindraje")

    @api.onchange('placa', 'marca', 'modelo', 'anio', 'color')
    def update_name(self):
        if self.placa or self.marca or self.modelo or self.anio or self.color:
            name_parts = [part for part in [self.placa, self.marca, self.modelo, str(self.anio), self.color] if part]
            self.name = ' '.join(name_parts)