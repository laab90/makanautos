# -*- coding: utf-8 -*-
import logging
import binascii
import codecs
from io import  BytesIO
from PIL import Image
import requests
from odoo import fields, models, api, _
from odoo.addons.odoo_multi_connect_sales_aagam.tools import chunks,  DomainVals, ReverseDict
_logger = logging.getLogger(__name__)

HelpImportOrderDate  = _(
"""A date used for selecting orders created after (or at) a specified time."""
)

HelpUpdateOrderDate = _(
"""
    A date used for selecting orders that were last updated after (or at) a specified time.
     An update is defined as any change in order status,includes updates made by the seller.
"""
)


class WooCommerceChannelSale(models.Model):
    _name = "woo.comm.channel.sale"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def get_channel(self):
        channel_list = []
        return channel_list

    def test_connection(self):
        self.ensure_one()
        if hasattr(self, 'test_%s_connection' % self.channel):
            return getattr(self, 'test_%s_connection' % self.channel)()

    def set_to_draft(self):
        self.state = 'draft'

    def display_message(self, message):
        wizard_id = self.env['wizard.message'].create({'text': message})
        return {
            'name': _("Summary"),
            'view_mode': 'form',
            'view_id': self.env.ref('odoo_multi_connect_sales_aagam.wizard_message_form').id,
            'res_model': 'wizard.message',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }

    def open_mapping_view(self):
        self.ensure_one()
        res_model = self._context.get('mapping_model')
        domain = [('channel_id', '=', self.id)]
        mapping_ids = self.env[res_model].search(domain).ids
        return {
            'name': ('Mapping'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': res_model,
            'view_id': False,
            'domain': [('id', 'in', mapping_ids)],
            'target': 'current',
        }

    def call_action_view(self):
        model_data = {
            'product.product': 'product.mapping',
            'product.template': 'template.mapping',
            'res.partner': 'partner.mapping',
            'product.category': 'woo.comm.product.category.mapping',
            'sale.order': 'order.mapping',
        }
        self.ensure_one()
        mapping_model = self._context.get('mapping_model')
        odoo_mapping_field = self._context.get('odoo_mapping_field')
        domain = [('channel_id', '=', self.id)]
        erp_ids = self.env[mapping_model].search(domain).mapped(odoo_mapping_field)
        erp_model = ReverseDict(model_data).get(mapping_model)
        if erp_model:
            return {
                'name': ('Record'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': erp_model,
                'view_id': False,
                'domain': [('id', 'in', erp_ids)],
                'target': 'current',
            }


    def _get_search_count(self):
        domain = [('channel_id', '=', (self.id))]
        products = self.env['template.mapping'].search_count(domain)
        categories = self.env['woo.comm.product.category.mapping'].search_count(domain)
        orders = self.env['order.mapping'].search_count(domain)
        domain += [('type', '=', 'contact')]
        customers = self.env['partner.mapping'].search_count(domain)
        self.channel_products = (products)
        self.channel_categories = (categories)
        self.channel_orders = (orders)
        self.channel_customers = (customers)

    active = fields.Boolean(
        string='Active',
        default=True
    )
    color = fields.Integer(string='Color Index')
    channel = fields.Selection(
        selection='get_channel',
        string="Channel",
        required=True
    )
    name = fields.Char(
        string='Name',
        required=True
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('validate', 'Validate'),
            ('error', 'Error')
        ],
        default='draft'
    )
    debug = fields.Selection(
        [
            ('enable', 'Enable'),
            ('disable', 'Disable')
        ],
        default='enable',
        required=True
    )
    environment = fields.Selection(
        [
            ('production', 'Production Server'),
            ('sandbox', 'Testing(Sandbox) Server)')
        ],
        string='Environment',
        default='sandbox',
        help="""Set environment to  production while using live credentials.""",
    )
    sku_sequence_id = fields.Many2one(
        'ir.sequence',
        help="""Default sequence used as sku/default code for product(in case product not have sku/default code).""",
        string='Sequence For SKU',
    )
    language_id = fields.Many2one(
        'res.lang',
        string='Language',
        default = lambda self: self.env['res.lang'].search([], limit=1),
        help="""The language used over e-commerce store/marketplace.""",

    )
    pricelist_id = fields.Many2one(
        'pricelist.mapping',
        string='Pricelist Mapping'
    )
    pricelist_name = fields.Many2one(
        'product.pricelist',
        string='Default Pricelist',
        default=lambda self: self.env['product.pricelist'].search([], limit=1),
        help="""Select the same currency of pricelist used  over e-commerce store/marketplace.""",

    )
    default_category_id = fields.Many2one(
        'product.category',
        help="""Default category used as product internal category for imported products.""",
        string='Category',
        default=lambda self: self.env['product.category'].search([], limit=1)
    )
    delivery_product_id = fields.Many2one(
        'product.product',
        help="""Delivery product used in sale order line.""",
        string='Delivery Product',
        domain=[('type', '=', 'service')],
    )
    discount_product_id = fields.Many2one(
        'product.product',
        help="""Discount product used in sale order line.""",
        string='Discount Product',
        domain=[('type', '=', 'service')],
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='WareHouse',
        default=lambda self: self.env['stock.warehouse'].search([], limit=1),
        help='WareHouse used for imported product.',
    )
    location_id = fields.Many2one(
        related='warehouse_id.lot_stock_id',
        string='Stock Location',
        help='Stock Location used for imported product.',
    )
    crm_team_id = fields.Many2one(
        'crm.team',
        string='Sales Team',
        default=lambda self: self.env['crm.team'].search([], limit=1),
        help='Sales Team used for imported order.',
    )
    order_state_ids = fields.One2many(
        'woo.comm.sale.order.state', 'channel_id',
        string='Default Odoo Order States',
        help='Imported order will process in odoo on basis of these state mappings.',
    )

    feed = fields.Selection(
        [
            ('all', 'For All Models'),
            ('order', 'For Order Only'),
        ],
        string='Feed',
        default='all',
        required=True
    )
    auto_evaluate_feed = fields.Boolean('Auto Evaluate Feed',
        default=1, help='Auto Evaluate Feed Just After Import.')
    auto_sync_stock = fields.Boolean('Auto Sync Stock',
        default=0, help='Enable this for real time stock sync over channel.')
    import_order_date = fields.Datetime('Order Imported', help=HelpImportOrderDate)
    update_order_date = fields.Datetime('Order Updated', help=HelpUpdateOrderDate)
    import_product_date = fields.Datetime('Product Imported')
    update_product_price = fields.Boolean('Update Price')
    update_product_stock = fields.Boolean('Update Stock')
    update_product_image = fields.Boolean('Update Image')
    update_product_date = fields.Datetime('Product Updated')
    import_customer_date = fields.Datetime('Customer Imported')
    update_customer_date = fields.Datetime('Customer Updated')
    api_record_limit = fields.Integer('API Record Limit', default=100)
    channel_products = fields.Integer(compute='_get_search_count')
    channel_categories = fields.Integer(compute='_get_search_count')
    channel_orders = fields.Integer(compute='_get_search_count')
    channel_customers = fields.Integer(compute='_get_search_count')
    override_price = fields.Boolean('Override Product Price', default=False)

    @api.constrains('api_record_limit')
    def check_api_record_limit(self):
        if self.api_record_limit<=0:
            raise Warning("""The api record limit should be postive.""")


    @api.model
    def set_channel_cron(self,ref_name='',active=False):
        try:
            cron_obj= self.env.ref(ref_name,False)
            if cron_obj:cron_obj.sudo().write(dict(active=active))
        except Exception as e:
            _logger.error("#1SetCronError  \n %r"%(e))
            raise Warning(e)

    @api.model
    def get_data_isoformat(self,date_time):
        try:
            return date_time and fields.Datetime.from_string(date_time).isoformat()
        except Exception as e:
            _logger.info("==%r="%(e))



    @api.model
    def set_channel_date(self, operation = 'import',record = 'product'):
        current_date = fields.Datetime.now()
        if operation == 'import':
            if record == 'order':self.import_order_date = current_date
            elif record == 'product':self.import_product_date = current_date
            elif record == 'customer':self.import_customer_date = current_date
        else:
            if record == 'order':self.update_order_date = current_date
            elif record == 'product':self.update_product_date = current_date
            elif record == 'customer':self.update_customer_date = current_date
        return True


    def toggle_enviroment_value(self):
        production = self.filtered(
            lambda channel: channel.environment == 'production')
        production.write({'environment': 'sandbox'})
        (self - production).write({'environment': 'production'})
        return True


    def toggle_debug_value(self):
        enable = self.filtered(lambda channel: channel.debug == 'enable')
        enable.write({'debug': 'disable'})
        (self - enable).write({'debug': 'enable'})
        return True


    def toggle_active_value(self):
        for record in self:
            record.write({'active': not record.active})
        return True


    @api.model
    def om_format_date(self, date_string):
        om_date = None
        message = ''
        try:
            if date_string:om_date = fields.Date.from_string(date_string)
        except Exception as e:
            message += '%r'%e
        return dict(
        message = message,
        om_date = om_date
        )

    @api.model
    def om_format_date_time(self, date_time_string):
        om_date_time = None
        message = ''
        try:
            if date_time_string:om_date_time = fields.Datetime.from_string(date_time_string)
        except Exception as e:
            message += '%r'%e
        return dict(
        message = message,
        om_date_time = om_date_time
        )

    @api.model
    def get_state_id(self, state_code, country_id, state_name=None):
        if (not state_code) and state_name:
            state_code = state_name[:2]
        state_name = state_name or ''
        domain = [
            ('code', '=', state_code),
            ('name', '=', state_name),
            ('country_id', '=', country_id.id)
        ]
        state_id = country_id.state_ids.filtered(
            lambda st:(
                st.code in [state_code,state_name[:3],state_name])
                or (st.name == state_name )
            )
        if not state_id:
            vals = DomainVals(domain)
            vals['name'] = state_name and state_name or state_code
            if (not vals['code']) and state_name:
                vals['code'] = state_name[:2]
            state_id = self.env['res.country.state'].create(vals)
        else:
            state_id =state_id[0]
        return state_id

    @api.model
    def get_country_id(self, country_code):
        domain = [
            ('code', '=', country_code),
        ]
        return self.env['res.country'].search(domain, limit=1)

    @api.model
    def get_currency_id(self, name):
        domain = [
            ('name', '=', name),
        ]
        return self.env['res.currency'].search(domain, limit=1)

    @api.model
    def create_model_objects(self, model_name, vals, **kwargs):

        message = ''
        data = None
        try:
            ObjModel = self.env[model_name]
            data = self.env[model_name]
            for val in vals:
                if kwargs.get('extra_val'):val.update( kwargs.get('extra_val'))
                match =False
                if val.get('store_id'):
                    obj = ObjModel.search([('store_id', '=', val.get('store_id'))],limit= 1)
                    if obj:
                        obj.write(val)
                        data += obj
                        match = True
                if not match :
                    data += ObjModel.create(val)
        except Exception as e:
            _logger.error("#1CreateModelObject Error  \n %r"%(e))
            message += "%r"%(e)
        return dict(
            data = data,
            message = message,
        )

    @api.model
    def create_product(self, name, _type='service', vals=None):
        vals = vals or {}
        vals['name'] = name
        vals['type'] = _type
        return self.env['product.product'].create(vals)

    @api.model
    def match_create_pricelist_id(self, currency_id):
        map_obj = self.env['pricelist.mapping']
        domain = [('store_currency_code', '=', currency_id.name)]
        match = self._match_mapping(map_obj, domain)
        if match:
            return match.odoo_pricelist_id
        else:
            pricelist_id = self.env['product.pricelist'].create(
                dict(
                    currency_id=currency_id.id,
                    name=self.name
                )
            )
            vals = dict(
                store_currency=currency_id.id,
                store_currency_code=currency_id.name,
                odoo_pricelist_id=pricelist_id.id,
                odoo_currency_id=currency_id.id,
            )
            return self._create_mapping(map_obj, vals).odoo_pricelist_id

    @api.model
    def get_uom_id(self, name):
        return self.env['uom.uom'].search([('name', '=', name)])

    @api.model
    def get_woo_comm_attribute_id(self, name, create_obj = False):
        match = self.env['product.attribute'].search([('name', '=', name)])
        if (not match) and create_obj:
            match = self.env['product.attribute'].create(DomainVals([('name', '=', name)]))
        return match

    @api.model
    def get_woo_comm_attribute_value_id(self, name, attribute_id, create_obj=False):
        match = self.env['product.attribute.value'].search([('name', '=', name), ('attribute_id', '=', attribute_id)])
        if (not match) and create_obj:
            match = self.env['product.attribute.value'].create(DomainVals([('name', '=', name), ('attribute_id', '=', attribute_id)]))
        return match

    @api.model
    def get_channel_domain_value(self, pre_domain=None):
        vals = []
        if type(self.id) == int:
            vals += [('channel_id', '=', self.id)]
        if pre_domain:
            vals += pre_domain
        return vals

    @api.model
    def get_channel_vals(self):
        return dict(
            channel_id=self.id,
            store_selection = self.channel
        )
    @api.model
    def _create_obj(self, obj, vals):
        channel_vals = self.get_channel_vals()
        if self._context.get('obj_type') == 'feed':
            channel_vals.pop('store_selection')
        vals.update(channel_vals)
        obj_id = obj.create(vals)
        return obj_id


    @api.model
    def _match_obj(self, obj, domain=None, limit=None):
        channel_domain = self.get_channel_domain_value(domain)
        new_domain = channel_domain
        if limit:
            return obj.search(new_domain, limit=limit)
        return obj.search(new_domain)


    @api.model
    def _create_mapping(self, mapping_obj, vals):
        return self._create_obj(mapping_obj, vals)


    @api.model
    def _match_mapping(self, mapping_obj, domain, limit=None):
        return self._match_obj(mapping_obj, domain, limit)


    @api.model
    def _create_feed(self, mapping_obj, vals):
        return self.with_context(obj_type='feed')._create_obj(mapping_obj, vals)


    @api.model
    def _match_feed(self, mapping_obj, domain, limit=None):
        return self._match_obj(mapping_obj, domain, limit)


    @api.model
    def _create_sync(self, vals):
        if self.debug=='enable':
            nvals = vals.copy()
            channel_vals = self.get_channel_vals()
            nvals.update(channel_vals)
            return self.env['sync.channel'].create(nvals)
        return self.env['sync.channel']


    @api.model
    def match_attribute_mappings(self, woo_comm_attribute_id=None,
    attribute_id=None,domain = None, limit=1):

        map_domain = self.get_channel_domain_value(domain)

        if woo_comm_attribute_id:
            map_domain += [('woo_comm_attribute_id', '=', woo_comm_attribute_id)]
        if attribute_id:
            map_domain += [('attribute_id', '=', attribute_id)]

        return self.env['woo.comm.attribute.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_attribute_value_mappings(self, woo_comm_attribute_value_id=None,
        attribute_value_id=None,domain = None, limit=1):

        map_domain = self.get_channel_domain_value(domain)
        if woo_comm_attribute_value_id:
            map_domain +=  [('woo_comm_attribute_value_id', '=', woo_comm_attribute_value_id)]
        if attribute_value_id:
            map_domain +=   [('attribute_value_id', '=', attribute_value_id)]
        return self.env['woo.comm.attribute.value.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_product_mappings(self, store_product_id=None, line_variant_ids=None,
            domain=None,limit=1,**kwargs):
        map_domain = self.get_channel_domain_value(domain)
        if store_product_id:
            map_domain+=[('store_product_id', '=', store_product_id), ]
        if line_variant_ids:
            map_domain += ['|', ('store_variant_id', '=', 'No Variants'),('store_variant_id', '=', line_variant_ids)]
        if kwargs.get('default_code'):
            map_domain += [('default_code', '=', kwargs.get('default_code'))]
        if kwargs.get('barcode'):
            map_domain += [('barcode', '=', kwargs.get('barcode'))]
        _logger.info("111===%r===="%(map_domain))
        return self.env['product.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_template_mappings(self, store_product_id = None, domain = None, limit = 1,**kwargs):
        map_domain = self.get_channel_domain_value(domain)
        if store_product_id:
            map_domain += [('store_product_id', '=', store_product_id)]
        if kwargs.get('default_code'):
            map_domain += [('default_code', '=', kwargs.get('default_code'))]
        if kwargs.get('barcode'):
            map_domain += [('barcode', '=', kwargs.get('barcode'))]
        return self.env['template.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_partner_mappings(self, store_id = None, _type='contact',domain=None, limit=1):
        map_domain = self.get_channel_domain_value(domain)+[('type', '=', _type)]
        if store_id:
            map_domain +=[('store_customer_id', '=', store_id)]
        return self.env['partner.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_order_mappings(self, store_order_id=None,domain=None, limit=1):
        map_domain = self.get_channel_domain_value(domain)
        if store_order_id:map_domain += [('store_order_id', '=', store_order_id)]
        return self.env['order.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_carrier_mappings(self, shipping_service_name=None, domain=None, limit=1):
        map_domain = self.get_channel_domain_value(domain)
        if shipping_service_name:map_domain +=[('shipping_service', '=', shipping_service_name)]
        return self.env['shipping.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_category_mappings(self, wc_product_categ_id=None, categ_id=None, domain=None, limit=1):
        map_domain = self.get_channel_domain_value(domain)
        if wc_product_categ_id:
            map_domain += [('wc_product_categ_id', '=', wc_product_categ_id)]
        if categ_id:
            map_domain += [('categ_id', '=', categ_id)]
        return self.env['woo.comm.product.category.mapping'].search(map_domain, limit=limit)


    @api.model
    def match_category_feeds(self, store_id=None,domain=None,limit=1):
        map_domain = self.get_channel_domain_value(domain)
        if store_id:map_domain  += [('store_id', '=', store_id)]
        return self.env['category.feed'].search(map_domain, limit=limit)


    @api.model
    def match_product_feeds(self, store_id=None,domain=None,limit=1):
        map_domain = self.get_channel_domain_value(domain)
        if store_id:map_domain  += [('store_id', '=', store_id)]
        return self.env['product.feed'].search(map_domain, limit=limit)


    @api.model
    def match_product_variant_feeds(self, store_id=None,domain=None,limit=1):
        map_domain = self.get_channel_domain_value(domain)
        if store_id:map_domain  += [('store_id', '=', store_id)]
        map_domain += [('feed_templ_id', '!=',False)]
        return self.env['product.variant.feed'].search(map_domain, limit=limit)


    @api.model
    def match_partner_feeds(self, store_id=None, _type='contact',domain=None,limit=1):
        map_domain = self.get_channel_domain_value(domain)+[('type', '=', _type)]
        if store_id:
            map_domain += [('store_id', '=', store_id)]
        return self.env['partner.feed'].search(map_domain, limit=limit)

    @api.model
    def match_order_feeds(self, store_id=None,domain=None,limit=1):
        map_domain = self.get_channel_domain_value(domain)
        if store_id:
            map_domain += [('store_id', '=', store_id)]

        return self.env['order.feed'].search(map_domain, limit=limit)

    @api.model
    def create_attribute_mapping(self, erp_id, store_id,woo_comm_attribute_name=''):
        self.ensure_one()
        if store_id and store_id not in ['0', -1]:
            vals = dict(
                woo_comm_attribute_id=store_id,
                woo_comm_attribute_name=woo_comm_attribute_name,
                attribute_id=erp_id.id,
                product_attribute_id=erp_id.id,
            )
            channel_vals = self.get_channel_vals()
            vals.update(channel_vals)
            return self.env['woo.comm.attribute.mapping'].create(vals)
        return self.env['woo.comm.attribute.mapping']

    @api.model
    def create_attribute_value_mapping(self, erp_id, store_id,woo_comm_attribute_value_name=''):
        self.ensure_one()
        if store_id and store_id not in ['0',' ', -1]:
            vals = dict(
                woo_comm_attribute_value_id=store_id,
                woo_comm_attribute_value_name=woo_comm_attribute_value_name,
                product_attribute_value_id=erp_id.id,
                attribute_value_id=erp_id.id,
            )
            channel_vals = self.get_channel_vals()
            vals.update(channel_vals)
            return self.env['woo.comm.attribute.value.mapping'].create(vals)
        return self.env['woo.comm.attribute.value.mapping']

    @api.model
    def create_partner_mapping(self, erp_id, store_id, _type):
        self.ensure_one()
        if store_id and store_id not in ['0', -1]:
            vals = dict(
                store_customer_id=store_id,
                odoo_partner_id=erp_id.id,
                odoo_partner=erp_id.id,
                type=_type,
            )
            channel_vals = self.get_channel_vals()
            vals.update(channel_vals)
            return self.env['partner.mapping'].create(vals)
        return self.env['partner.mapping']


    @api.model
    def create_carrier_mapping(self, name, service_id=None):
        carrier_obj = self.env['delivery.carrier']
        partner_id = self.env.user.company_id.partner_id
        carrier_vals = dict(
            product_id = self.delivery_product_id.id,
            name=name,
            fixed_price=0,
        )
        carrier_id = carrier_obj.sudo().create(carrier_vals)
        service_id = service_id and service_id or name
        vals = dict(
            shipping_service=name,
            shipping_service_id=service_id,
            wc_product_categ_id=name,
            odoo_carrier_id=carrier_id.id,
            odoo_shipping_carrier=carrier_id.id,
        )
        channel_vals = self.get_channel_vals()
        vals.update(channel_vals)
        vals.pop('wc_product_categ_id')
        self.sudo().env['shipping.mapping'].create(vals)
        return carrier_id


    @api.model
    def create_template_mapping(self, erp_id, store_id, vals=None):
        self.ensure_one()
        vals =vals or dict()
        vals.update(dict(
            store_product_id=store_id,
            odoo_template_id=erp_id.id,
            template_name=erp_id.id,
            default_code=vals.get('default_code'),
            barcode=vals.get('barcode'),
        ))
        channel_vals = self.get_channel_vals()
        vals.update(channel_vals)
        return self.env['template.mapping'].create(vals)


    @api.model
    def default_multi_channel_values(self):
        return self.env['res.config.settings'].sudo().get_values()



    @api.model
    def match_odoo_template(self, vals,variant_lines):
        Template = self.env['product.template']
        record = self.env['product.template']
        barcode = vals.get('barcode')
        if barcode:
            record = Template.search([('barcode', '=', barcode)], limit=1)
        if not record:
            ir_values = self.default_multi_channel_values()
            default_code = vals.get('default_code')
            if ir_values.get('is_duplicate_avoid') and default_code:
                record = Template.search([('default_code', '=', default_code)], limit=1)
            if not record:
                for var in variant_lines:
                    match = self.match_odoo_product(var.read([])[0])
                    if match:
                        record = match.product_tmpl_id
        return record


    @api.model
    def match_odoo_product(self, vals, obj='product.product'):
        oe_env = self.env[obj]
        record = False
        barcode = vals.get('barcode')
        if barcode:
            record = oe_env.search([('barcode', '=', barcode)], limit=1)
        if not record:
            default_code = vals.get('default_code')
            ir_values = self.default_multi_channel_values()
            if ir_values.get('is_duplicate_avoid') and default_code:
                record = oe_env.search([('default_code', '=', default_code)], limit=1)
        return record


    @api.model
    def create_product_mapping(self, odoo_template_id, odoo_product_id, store_id, store_variant_id, vals=None):
        self.ensure_one()
        vals = dict(vals or dict())
        vals.update(dict(
            store_product_id=store_id,
            store_variant_id=store_variant_id,
            erp_product_id=odoo_product_id.id,
            product_name=odoo_product_id.id,
            odoo_template_id=odoo_template_id.id,
            default_code=vals.get('default_code'),
            barcode=vals.get('barcode'),
        ))
        channel_vals = self.get_channel_vals()
        vals.update(channel_vals)
        return self.env['product.mapping'].create(vals)


    @api.model
    def create_category_mapping(self, erp_id, store_id, is_leaf_category=True):
        self.ensure_one()
        vals = dict(
            wc_product_categ_id=store_id,
            categ_id=erp_id.id,
            product_category_id=erp_id.id,
            is_leaf_category=is_leaf_category,
        )
        channel_vals = self.get_channel_vals()
        vals.update(channel_vals)
        return self.env['woo.comm.product.category.mapping'].create(vals)


    @api.model
    def create_order_mapping(self, erp_id, store_id,store_source=None):
        self.ensure_one()
        vals = dict(
            odoo_partner_id=erp_id.partner_id,
            store_order_id=store_id,
            store_id=store_source,
            odoo_order_id=erp_id.id,
            order_name=erp_id.id,
        )
        channel_vals = self.get_channel_vals()
        vals.update(channel_vals)
        return self.env['order.mapping'].create(vals)

    def open_website_url(self, url, name='Open Website URL'):
        self.ensure_one()
        return {
            'name': name,
            'url': url,
            'type': 'ir.actions.act_url',
            'target': 'new',
        }

    # check unused
    def sync_order_feeds(self, vals, **kwargs):
        message = ''
        try:
            partner_vals = kwargs.get('partner_vals')
            category_vals = kwargs.get('category_vals')
            product_vals = kwargs.get('product_vals')
            channel_vals = kwargs.get('channel_vals') or self.get_channel_vals()

            if partner_vals:
                message += self.sync_partner_feeds(
                    partner_vals, channel_vals= channel_vals)[0].get('message','')
            if kwargs.get('category_vals'):
                message += self.sync_category_feeds(
                    category_vals, channel_vals= channel_vals)[0].get('message','')
            if kwargs.get('product_vals'):
                message += self.sync_product_feeds(
                    product_vals, channel_vals= channel_vals)[0].get('message','')
            ObjModel = self.env['order.feed']
            for val in vals :
                obj = ObjModel.search([('store_id','=',val.get('store_id'))])
                obj.write(dict(line_ids=[(6,0,[])]))
            res = self.create_model_objects(
                'order.feed',vals,extra_val= channel_vals)
            message += res.get('message','')
            data = res.get('data')
            if data:
                for data_item in data:
                    import_res = data_item.import_order(self)
                    message += import_res.get('message', '')
        except Exception as e:
            _logger.error("#SyncOrderFeeds Error  \n %r"%(e))
            message += '%r'%(e)
        return dict(
            kwargs = kwargs,
            message = message
        )

    # check unused
    def sync_partner_feeds(self, vals, **kwargs):
        channel_vals = kwargs.get('channel_vals') or self.get_channel_vals()
        res= self.create_model_objects('partner.feed', vals, extra_val= channel_vals)
        message = res.get('message','')
        data = res.get('data')
        if data:
            for data_item in data:
                import_res = data_item.import_partner(self)
                message += import_res.get('message', '')
        return dict(
            message = message
        )

    # check unused
    def sync_category_feeds(self, vals, **kwargs):
        channel_vals = kwargs.get('channel_vals') or self.get_channel_vals()
        res = self.create_model_objects('category.feed', vals, extra_val = channel_vals)
        message = res.get('message','')
        data = res.get('data')
        if data:
            for data_item in data:
                import_res = data_item.import_category(self)
                message += import_res.get('message', '')
        return dict(message = message)

    # check unused
    def sync_product_feeds(self, vals, **kwargs):
        channel_vals = kwargs.get('channel_vals') or self.get_channel_vals()
        res = self.create_model_objects('product.feed', vals, extra_val= channel_vals)
        context = dict(self._context)
        ObjModel = self.env['product.feed']
        for val in vals :
            obj = ObjModel.search([('store_id','=',val.get('store_id'))])
            obj.write(dict(feed_variants=[(6,0,[])]))
        res= self.with_context(context).create_model_objects('product.feed',vals,extra_val=channel_vals)
        message = res.get('message','')
        data = res.get('data')
        if data:
            for data_item in data:
                import_res = data_item.import_product(self)
                message += import_res.get('message', '')
        return dict(
            message = message
        )

    @staticmethod
    def read_website_image_url(image_url):
        data = None
        try:
            res = requests.get(image_url)
            if res.status_code == 200:
                data = binascii.b2a_base64((res.content))
        except Exception as e:
            _logger.error("#1ReadImageUrlError  \n %r"%(e))
        return data

    # check unused
    @api.model
    def _match_create_product_categ(self, vals):
        match = self.match_category_feeds(store_id= vals.get('store_id'))
        feed_obj = self.env['category.feed']
        update = False
        if match:
            vals['state'] = 'update'
            vals.pop('store_id','')
            update = match.write(vals)
            data = match
        else:
            data = self._create_feed(feed_obj, vals)
        return dict(
            data = data,
            update = update
        )

    @api.model
    def get_channel_category_id(self, template_id, channel_id, limit=1):
        extra_categ_ids = (template_id.extra_categ_ids or
        template_id.categ_id.extra_categ_ids)
        channel_categ = extra_categ_ids.filtered(
            lambda cat: cat.instance_id == channel_id
        )
        extra_category_ids = channel_categ.mapped('extra_category_ids')
        domain = []
        if extra_category_ids:
            domain = [('categ_id', 'in', extra_category_ids.ids)]
        return channel_id.match_category_mappings(domain=domain, limit=limit).mapped('wc_product_categ_id')

    @api.model
    def set_order_by_status(self,channel_id,store_id,
            status,order_state_ids,default_order_state,
            payment_method = None):
        result = dict(order_match = None, message = '')
        order_match = channel_id.match_order_mappings(store_id)
        order_state_ids = order_state_ids.filtered(
            lambda state: state.channel_state == status)
        if order_state_ids:
            state = order_state_ids[0]
        else:
            state = default_order_state
        if order_match  and order_match.order_name.state =='draft' and (
                state.odoo_create_invoice or state.odoo_ship_order):
            result['message'] += self.env['multi.channel.skeleton']._SetOdooOrderState(
                order_match.order_name, channel_id,  status, payment_method
            )
            result['order_match']=order_match
        return result

    @staticmethod
    def get_image_type(image_data):
        image_stream = BytesIO(codecs.decode(image_data, 'base64'))
        image = Image.open(image_stream)
        image_type = image.format.lower()
        if not image_type:
            image_type = 'jpg'
        return image_type
