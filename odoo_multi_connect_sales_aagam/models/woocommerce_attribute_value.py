# -*- coding: utf-8 -*-
from odoo import fields , models,api

class WooCommAttributetMapping(models.Model):
    _name = "woo.comm.attribute.mapping"
    _inherit = ['woo.comm.channel.mapping']

    woo_comm_attribute_id =  fields.Char('WooCommerce Product Attribute' ,required=True)
    woo_comm_attribute_name =  fields.Char('WooCommerce Product Attribute Name' )
    product_attribute_id = fields.Many2one('product.attribute', 'Product Attribute', required=True)
    attribute_id = fields.Integer('Odoo Attribute ID', required=True)

    def _compute_name(self):
        for record in self:
            if record.product_attribute_id:
                record.name = record.product_attribute_id.name
            else:
                record.name = 'Deleted'

    @api.onchange('product_attribute_id')
    def onchnage_product_attribute_id(self):
        for record in self:
            record.attribute_id = record.product_attribute_id.id


class WooCommAttributeValueMapping(models.Model):
    _name="woo.comm.attribute.value.mapping"
    _inherit = ['woo.comm.channel.mapping']

    woo_comm_attribute_value_id = fields.Char('WooCommerce Product Attribute Value', required=True)
    woo_comm_attribute_value_name = fields.Char('WooCommerce Product Attribute Name')
    product_attribute_value_id = fields.Many2one('product.attribute.value', 'Product Attribute Name', required=True)
    attribute_value_id = fields.Integer('Product Attribute Value ID', required=True)

    @api.onchange('product_attribute_value_id')
    def onchange_product_attribute_value_id(self):
        for record in self:
            record.attribute_value_id = record.product_attribute_value_id.id

    def _compute_name(self):
        for record in self:
            if record.product_attribute_value_id:
                record.name = record.product_attribute_value_id.name
            else:
                record.name = 'Deleted'
