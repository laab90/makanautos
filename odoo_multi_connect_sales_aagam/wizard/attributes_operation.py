# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ImportAttribute(models.TransientModel):
    _inherit = ['import.operation']
    _name = "import.attributes"

    attribute_ids = fields.Text('Attribute ID(s)')


class ExportAttribute(models.TransientModel):
    _inherit = ['export.operation']
    _name = "export.attributes"

    @api.model
    def default_get(self,fields):
        res=super(ExportAttribute,self).default_get(fields)
        if not res.get('attribute_ids') and self._context.get('active_model') == 'product.attribute':
            res['attribute_ids'] = self._context.get('active_ids')
        return res

    attribute_ids = fields.Many2many('product.attribute', string='Attribute(s)')

class ImportAttributeValue(models.TransientModel):
    _inherit = ['import.operation']
    _name = "import.attributes.value"

    product_template_attribute_value_ids = fields.Text('Attribute Value ID(s)')

class ExportAttributeValue(models.TransientModel):
    _inherit = ['export.operation']
    _name = "export.attributes.value"

    @api.model
    def default_get(self,fields):
        res = super(ExportAttributeValue,self).default_get(fields)
        if not res.get('product_template_attribute_value_ids') and self._context.get('active_model')=='product.attribute.value':
            res['product_template_attribute_value_ids']=self._context.get('active_ids')
        return res

    product_template_attribute_value_ids = fields.Many2many('product.attribute.value', string='Attribute(s)')
