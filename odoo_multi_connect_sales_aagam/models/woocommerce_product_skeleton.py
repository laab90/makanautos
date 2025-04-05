# -*- coding: utf-8 -*-
from odoo import fields, models, api


class TemplateMapping(models.Model):
    _name = "template.mapping"
    _inherit = ['woo.comm.channel.mapping']

    store_product_id = fields.Char('Store Product ID', required=True)
    odoo_template_id = fields.Char('Odoo Template ID', required=True)
    template_name = fields.Many2one('product.template', 'Product Template')
    default_code = fields.Char("Default code/SKU")
    barcode = fields.Char("Barcode/EAN/UPC or ISBN")

    def unlink(self):
        for record in self:
            if record.store_product_id:
                match = record.channel_id.match_product_feeds(record.store_product_id)
                if match: match.unlink()
        return super(TemplateMapping, self).unlink()

    def _compute_name(self):
        for record in self:
            if record.template_name:
                record.name = record.template_name.name
            else:
                record.name = 'Deleted/Undefined'

    @api.onchange('template_name')
    def change_odoo_id(self):
        self.odoo_template_id = self.template_name.id


class ProductMappings(models.Model):
    _name = "product.mapping"
    _inherit = ['woo.comm.channel.mapping']

    store_product_id = fields.Char('Store Template ID', required=True)
    store_variant_id = fields.Char('Store Varinat ID', required=True, default='No Variants')
    erp_product_id = fields.Integer('Odoo Variant ID', required=True)
    product_name = fields.Many2one('product.product', 'Product', required=True)
    odoo_template_id = fields.Many2one(
        related='product_name.product_tmpl_id',
        string='Odoo Template')
    default_code = fields.Char("Default code/SKU")
    barcode = fields.Char("Barcode/EAN/UPC or ISBN")

    def _compute_name(self):
        for record in self:
            if record.product_name.name:
                record.name = record.product_name.name
            else:
                record.name = 'Deleted'

    @api.onchange('product_name')
    def change_odoo_id(self):
        self.erp_product_id = self.product_name.id
        self.odoo_template_id = self.product_name.product_tmpl_id.id
