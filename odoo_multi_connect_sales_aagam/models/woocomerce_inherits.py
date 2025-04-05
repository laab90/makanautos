# -*- coding: utf-8 -*-
import itertools
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    length = fields.Float('Length')
    width = fields.Float('Width')
    height = fields.Float('Height')
    image_url = fields.Char('Image Url')
    measure_id = fields.Many2one('uom.uom', 'Unit of Measure', help="Default Unit of Measure used for dimension.")
    channel_mapping_ids = fields.One2many('template.mapping', 'template_name', string='Mappings', copy=False)
    extra_categ_ids = fields.One2many('extra.product.categories', 'product_id', string='Extra Categories')
    channel_sale_ids = fields.Many2many(
        'woo.comm.channel.sale',
        'product_tmp_channel_rel',
        'product_tmpl_id',
        'channel_id',
        string='Channel(s)')
    product_id_type = fields.Selection(
        [('upc_no', 'UPC'),
            ('ean_no', 'EAN'),
            ('isbn_no', 'ISBN'),
        ],
        string='Product ID Type',
        default='upc_no',
    )


class ExtraProductCategories(models.Model):
    _name = 'extra.product.categories'

    @api.model
    def get_category_list(self):
        li = []
        category_ids_list = self.env['woo.comm.product.category.mapping'].search([('channel_id', '=', self.instance_id.id)])
        if category_ids_list:
            for i in category_ids_list:
                li.append(i.categ_id)
        return li

    @api.depends('instance_id')
    def _compute_extra_categories_domain(self):
        for record in self:
            categ_list = record.get_category_list()
            record.extra_category_domain_ids = [(6, 0, categ_list)]

    instance_id = fields.Many2one('woo.comm.channel.sale', 'Instance')
    product_id = fields.Many2one('product.template', 'Template')
    category_id = fields.Many2one('product.category', 'Internal Category')
    extra_category_ids = fields.Many2many('product.category', string='Extra Categories', domain="[('id', 'in', extra_category_domain_ids)]")
    extra_category_domain_ids = fields.Many2many(
        "product.category",
        'extra_categ_ref',
        'product_categ_ref',
        'table_ref',
        compute="_compute_extra_categories_domain",
        string="Category Domain",
    )

    @api.onchange('instance_id')
    def change_domain(self):
        categ_list = self.get_category_list()
        domain = {'domain': {'extra_category_ids': [('id', 'in', categ_list)]}}
        return domain


class ProductCategory(models.Model):
    _inherit = "product.category"

    channel_mapping_ids = fields.One2many( 'woo.comm.product.category.mapping', 'product_category_id',
        string='Mappings',copy=False)

    extra_categ_ids = fields.One2many('extra.product.categories', 'category_id',
        string='Channel Categories', copy=False)


class ProductProduct(models.Model):
    _inherit = "product.product"

    channel_mapping_ids = fields.One2many('product.mapping', 'product_name',
        string='Mappings', copy=False)

    @api.model
    def get_product_attribute_id(self, attribute_id):
        product_attribute_id = 0
        context = dict(self._context or {})
        attribute_map_domain = [
            ('channel_id', '=', context.get('channel_id'))]
        woo_comm_attribute_id = ''
        map_env = self.env[
            'woo.comm.attribute.mapping']
        if attribute_id.get('attrib_name_id'):
            woo_comm_attribute_id = attribute_id.get('attrib_name_id')
        else:
            woo_comm_attribute_id = attribute_id.get('name')
        attribute_mapping = map_env.search([('channel_id', '=', context.get(
            'channel_id')), ('woo_comm_attribute_id', '=', woo_comm_attribute_id)], limit=1)
        if not attribute_mapping:
            product_attribute = self.env['product.attribute'].search(
                [('name', '=', attribute_id.get('name'))])
            if not product_attribute:
                product_attribute_id = self.env['product.attribute'].create(
                    {'name': attribute_id.get('name')}).id
            else:
                product_attribute_id = product_attribute[0].id
            vals = {
                'woo_comm_attribute_id': woo_comm_attribute_id,
                'woo_comm_attribute_name': attribute_id.get('name'),
                'product_attribute_id': product_attribute_id,
                'attribute_id': product_attribute_id,
                'channel_id': context.get('channel_id'),
                'store_selection': context.get('channel')
            }
            map_env.create(vals)
        else:
            product_attribute_id = attribute_mapping.attribute_id
        return product_attribute_id

    @api.model
    def get_product_attribute_value_id(self, attribute_id, product_attribute_id, template_id):
        product_attribute_value_id = 0
        context = dict(self._context or {})
        woo_comm_attribute_value_id = ''
        map_env = self.env['woo.comm.attribute.value.mapping']
        if attribute_id.get('attrib_value_id'):
            woo_comm_attribute_value_id = attribute_id.get('attrib_value_id')
        else:
            woo_comm_attribute_value_id = attribute_id.get('value')
        attribute_value_mapping = self.env[
            'woo.comm.attribute.value.mapping'].search([
                ('channel_id', '=', context.get('channel_id')),
                ('woo_comm_attribute_value_id', '=', woo_comm_attribute_value_id),
				('product_attribute_value_id.attribute_id','=',product_attribute_id)], limit=1)
        if not attribute_value_mapping:
            product_attribute_value = self.env['product.attribute.value'].search([
                ('name', '=', attribute_id.get('value')),
                ('attribute_id', '=', product_attribute_id),
            ])

            if not product_attribute_value:
                context['active_id'] = template_id.id
                product_attribute_value_id = self.env['product.attribute.value'].with_context(context).create(
                    {'name': attribute_id.get('value'),
                     'attribute_id': product_attribute_id
                     }).id

            else:
                product_attribute_value_id = product_attribute_value[0].id
            map_env.create({
                'woo_comm_attribute_value_id': woo_comm_attribute_value_id,
                'woo_comm_attribute_value_name': attribute_id.get('value'),
                'product_attribute_value_id': product_attribute_value_id,
                'attribute_value_id': product_attribute_value_id,
                'channel_id': context.get('channel_id'),
                'store_selection': context.get('channel')
            })
        else:
            product_attribute_value_id = attribute_value_mapping.attribute_value_id
        return product_attribute_value_id

    def check_for_new_attrs(self, template_id, variant):
        context = dict(self._context or {})
        product_template = self.env['product.template']
        product_attribute_line = self.env['product.template.attribute.line']
        all_values = []
        attributes = variant.name_value
        for attribute_id in eval(attributes):
            product_attribute_id = self.get_product_attribute_id(attribute_id)
            product_attribute_value_id = self.get_product_attribute_value_id(
                attribute_id, product_attribute_id, template_id)
            exists = product_attribute_line.search(
                [('product_tmpl_id', '=', template_id.id),
                 ('attribute_id', '=', product_attribute_id)
                 ])
            if not exists:
                temp = {'product_tmpl_id': template_id.id,
                        'attribute_id': product_attribute_id,
                        'value_ids': [[4, product_attribute_value_id]]}
                pal_id = product_attribute_line.create(temp)
            # else:
            #     pal_id = exists[0]
            # value_ids = pal_id.value_ids.ids

            # if product_attribute_value_id not in value_ids:
            #     pal_id.write({'value_ids': [[4, product_attribute_value_id]]})
            # if product_attribute_value_id not in all_values:
            #     all_values.append(product_attribute_value_id)
            # return [(6, 0, all_values)]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    channel_mapping_ids = fields.One2many(
        'order.mapping', 'order_name',
        string='Mappings', copy=False)




class ResPartner(models.Model):
    _inherit = "res.partner"

    channel_mapping_ids = fields.One2many(
        'partner.mapping', 'odoo_partner',
        string='Mappings', copy=False)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    channel_mapping_ids = fields.One2many(
        'shipping.mapping', 'odoo_shipping_carrier',
        string='Mappings', copy=False)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_paid(self):
        self.action_confirm_pre_paid()
        result = super(AccountMove, self).action_invoice_paid()
        self.action_confirm_post_paid(result)
        return result

    def get_invoice_order(self, invoice):
        data = map(
            lambda line_id:
            list(set(line_id.sale_line_ids.mapped('order_id'))),
            invoice.invoice_line_ids
        )
        return list(itertools.chain(*data))

    def action_confirm_pre_paid(self):
        for invoice in self:
            order_ids = self.get_invoice_order(invoice)
            for order_id in order_ids:
                mapping_ids = order_id.channel_mapping_ids
                channel_id = mapping_ids.mapped('channel_id')
                channel_id = channel_id and channel_id[0] or channel_id
                if hasattr(channel_id, '%s_pre_confirm_paid' % channel_id.channel):
                    res = getattr(channel_id,
                                  '%s_pre_confirm_paid' % channel_id.channel)(invoice, mapping_ids)
        return True

    def action_confirm_post_paid(self, result):
        for invoice in self:
            order_ids = self.get_invoice_order(invoice)
            for order_id in order_ids:
                mapping_ids = order_id.channel_mapping_ids
                channel_id = mapping_ids.mapped('channel_id')
                channel_id = channel_id and channel_id[0] or channel_id
                if hasattr(channel_id, '%s_post_confirm_paid' % channel_id.channel):
                    res = getattr(channel_id,
                                  '%s_post_confirm_paid' % channel_id.channel)(invoice, mapping_ids, result)
        return True


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        self.ensure_one()
        self.do_pre_transfer()
        result = super(StockPicking, self).action_done()
        self.do_post_transfer(result)
        return result

    def do_pre_transfer(self):
        order_id = self.sale_id
        if order_id:
            mapping_ids = order_id.channel_mapping_ids
            channel_id = mapping_ids.mapped('channel_id')
            channel_id = channel_id and channel_id[0] or channel_id
            if hasattr(channel_id, '%s_pre_do_transfer' % channel_id.channel):
                res = getattr(channel_id,
                              '%s_pre_do_transfer' % channel_id.channel)(self, mapping_ids)
        return True

    def do_post_transfer(self, result):
        order_id = self.sale_id
        if order_id:
            mapping_ids = order_id.channel_mapping_ids
            channel_id = mapping_ids.mapped('channel_id')
            channel_id = channel_id and channel_id[0] or channel_id
            if hasattr(channel_id, '%s_post_do_transfer' % channel_id.channel):
                res = getattr(channel_id,
                              '%s_post_do_transfer' % channel_id.channel)(self, mapping_ids, result)
        return True


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    @api.model
    def create(self, vals):
        context = self._context
        if context.get('odoo_multi_attribute') or context.get('install_mode'):
            domain = [('name', '=ilike', vals.get('name').strip(' '))]
            obj = self.search(domain, limit=1)
            if obj:
                return obj
        return super(ProductAttribute, self).create(vals)
