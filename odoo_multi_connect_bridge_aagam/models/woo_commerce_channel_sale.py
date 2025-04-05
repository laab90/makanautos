# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import logging
from urllib import parse as urlparse
import re
remove_tag = re.compile(r'<[^>]+>')

_logger = logging.getLogger(__name__)
try:
    from woocommerce import API
except ImportError:
    _logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')


class WooCommerceChannelSale(models.Model):
    _inherit = "woo.comm.channel.sale"

    def get_channel(self):
        res = super(WooCommerceChannelSale, self).get_channel()
        res.append(('woocommerce', "WooCommerce"))
        return res

    url = fields.Char("Url", help='eg. https://www.aagaminfotech.com')
    consumer_key = fields.Char('Consumer Key', help='eg. ck_ccac94fc4362ba12a2045086ea9db285e8f02ac9')
    secret_key = fields.Char('Secret Key', help='eg. cs_a4c0092684bf08cf7a83606b44c82a6e0d8a4cae')
    woocommerce_interval_type = fields.Selection(
        [
            ('minutes', 'Minutes'),
            ('hours', 'Hour'),
            ('days', 'Day')
        ],
        string="Interval Type", default="hours")
    woocommerce_intervals = fields.Integer('Intervals', default=1)
    woocommerce_feed_cron = fields.Boolean('Feed Evaluate', help="Enable to run feed cron")
    woocommerce_is_import = fields.Boolean("Import", default=False,
                                           help="For import product, customers via Cron Enable it to run cron")
    woocommerce_is_export = fields.Boolean("Export", default=False,
                                           help="For export of products, categories, attribute and it's values Via Cron, Enable it to run cron from Odoo to woocommerce")

    def string_parsed_time(self, date_str):
        if not date_str:
            return False
        if not isinstance(date_str, str):
            date_str = str(date_str)
        date_str = date_str.split()
        _logger.info("======>%r", date_str[1])
        return date_str[0], date_str[1]

    def get_import_date(self):
        date = ''
        if 'name' in self._context:
            if self._context['name'] == 'product':
                date_str, time = self.string_parsed_time(self.import_product_date)
                if not date_str:
                    return False
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            elif self._context['name'] == 'order':
                date_str, time = self.string_parsed_time(self.import_order_date)
                if not date_str:
                    return False
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            elif self._context['name'] == 'customer':
                date_str, time = self.string_parsed_time(self.import_customer_date)
                if not date_str:
                    return False
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                raise UserError(_('Context Empty'))
        date = date - timedelta(days=1)
        return str(date) + "T" + str(time)

    def get_update_date(self):
        date = ''
        if 'name' in self._context:
            if self._context['name'] == 'product':
                date_str, time = self.string_parsed_time(self.update_product_date)
                if not date_str:
                    return False
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            elif self._context['name'] == 'order':
                date_str, time = self.string_parsed_time(self.update_order_date)
                if not date_str:
                    return False
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            elif self._context['name'] == 'customer':
                date_str, time = self.string_parsed_time(self.update_customer_date)
                if not date_str:
                    return False
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            elif self._context['name'] == 'category':
                date_str, time = self.string_parsed_time(self.update_product_date)
                if not date_str:
                    return False
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                raise UserError(_('Context Empty'))
        date = date - timedelta(days=1)
        date = str(date)
        return date + "T" + str(time)

    def test_woocommerce_connection(self):
        message = ""
        woocommerce = API(
            url=self.url,
            consumer_key=self.consumer_key,
            consumer_secret=self.secret_key,
            wp_api=True,
            version="wc/v3",
            timeout=30,
            query_string_auth=True,
        )
        try:
            woocommerce_api = woocommerce.get('system_status')
        except Exception as e:
            raise UserError(_("Error:" + str(e)))
        if 'message' in woocommerce_api.json():
            message = "Connection Error" + str(woocommerce_api.status_code) + " : " + str(woocommerce_api.text)
            raise UserError(_(message))
        else:
            self.state = 'validate'
            message = "Connection Successful!!"
        return self.display_message(message)

    def get_woo_comm_connection(self):
        woocommerce = API(
            url=self.url,
            consumer_key=self.consumer_key,
            consumer_secret=self.secret_key,
            wp_api=True,
            version="wc/v3",
            timeout=30,
            query_string_auth=True,
            verify_ssl=False,
        )
        try:
            woocommerce_api = woocommerce.get('system_status')
        except Exception as e:
            raise UserError(_("Error:" + str(e)))
        if 'message' in woocommerce_api.json():
            message = "Connection Error" + str(woocommerce_api.status_code) + " : " + str(woocommerce_api.text)
            raise UserError(_(message))
        else:
            return woocommerce

    def update_woo_comm_qty(self, woocommerce, quantity, product_map_rec):
        if woocommerce and product_map_rec:
            if product_map_rec.store_variant_id == 'No Variants':
                product_dict = woocommerce.get('products/' + str(product_map_rec.store_product_id)).json()
                if "bundle_layout" in product_dict:
                    product_dict.pop("bundle_layout")
                if product_dict['stock_quantity'] is None:
                    product_dict['stock_quantity'] = 0
                quantity = int(product_dict['stock_quantity'] + quantity)
                product_dict.update({'stock_quantity': quantity})
                try:
                    return_dict = woocommerce.put('products/' + str(product_map_rec.store_product_id),
                                                  product_dict).json()
                    if 'message' in return_dict:
                        raise UserError(_("Can't update product stocks , " + str(return_dict['message'])))
                except Exception as e:
                    raise UserError(_("Can't update product stocks, " + str(e)))
            else:
                variant_dict = woocommerce.get('products/' + str(
                    product_map_rec.store_product_id) + "/variations/" + product_map_rec.store_variant_id).json()
                if variant_dict['stock_quantity'] is None:
                    variant_dict['stock_quantity'] = 0
                quantity = int(variant_dict['stock_quantity'] + quantity)
                variant_dict.update({'stock_quantity': quantity})
                try:
                    return_dict = woocommerce.put('products/' + str(
                        product_map_rec.store_product_id) + "/variations/" + product_map_rec.store_variant_id,
                                                  variant_dict).json()
                    if 'message' in return_dict:
                        raise UserError(_("Can't update product stocks , " + str(return_dict['message'])))
                except Exception as e:
                    raise UserError(_("Can't update product stocks, " + str(e)))
        return True

    def woo_comm_do_post_transfer(self, stock_picking, mapping_ids, result):
        order_status = self.order_state_ids.filtered('odoo_ship_order')[0]
        status = order_status.channel_state
        woocommerce_order_id = mapping_ids.store_order_id
        wcapi = self.get_woo_comm_connection()
        data = wcapi.get('orders/' + woocommerce_order_id).json()
        data.update({'status': status})
        msg = wcapi.put('orders/' + woocommerce_order_id, data)

    def woo_comm_do_post_paid(self, invoice, mapping_ids, result):
        order_status = self.order_state_ids.filtered(lambda state: state.odoo_set_invoice_state == 'paid')[0]
        status = order_status.channel_state
        woocommerce_order_id = mapping_ids.store_order_id
        wcapi = self.get_woo_comm_connection()
        data = wcapi.get('orders/' + woocommerce_order_id).json()
        data.update({'status': status})
        msg = wcapi.put('orders/' + woocommerce_order_id, data)

    @api.model
    def import_order_cron(self):
        all_channel = self.env['woo.comm.channel.sale'].search([('channel', '=', 'woocommerce')])
        for channel in all_channel:
            if channel.woocommerce_is_import:
                try:
                    channel.import_woo_comm_sale_orders()
                except Exception as e:
                    _logger.info("Oops!!==Order Evaluate Failed (WooCommerce)====(%r)====(%r)", channel, e)
                    continue
        return True

    def write(self, vals):
        status = super(WooCommerceChannelSale, self).write(vals)
        for channel_id in self:
            if channel_id.channel == 'woocommerce':
                if ('woocommerce_is_import' in vals) or ('woocommerce_intervals' in vals) or (
                        'woocommerce_interval_type' in vals) or ('woocommerce_feed_cron' in vals):
                    channel_id.sudo().get_woo_comm_cron()
        return status

    def get_woo_comm_cron(self):
        self.sudo().chnage_woo_comm_cron_state()
        self.sudo().set_woo_comm_interval()
        self.sudo().change_woo_comm_feed_cron()

    def chnage_woo_comm_cron_state(self):
        import_vals = {'active': self.woocommerce_is_import}
        self.env.ref('odoo_multi_connect_bridge_aagam.ir_cron_import_woo_comm_sale_orders').write(import_vals)

    def set_woo_comm_interval(self):
        vals = {'interval_type': self.woocommerce_interval_type, 'interval_number': self.woocommerce_intervals}
        self.env.ref('odoo_multi_connect_bridge_aagam.ir_cron_import_woo_comm_sale_orders').write(vals)

    def change_woo_comm_feed_cron(self):
        vals = {'active': self.woocommerce_feed_cron}
        self.env.ref('odoo_multi_connect_sales_aagam.cron_import_product').write(vals)
        self.env.ref('odoo_multi_connect_sales_aagam.cron_import_category').write(vals)
        self.env.ref('odoo_multi_connect_sales_aagam.cron_import_partner').write(vals)

    def export_woo_comm_all_vals(self):
        attr_val = 0
        attribute_value_records = ''
        attribute_value_records = self.env['product.attribute.value'].search([])
        for attribute_value in attribute_value_records:
            mapping_rec = self.env['woo.comm.attribute.value.mapping'].search(
                [('attribute_value_id', '=', attribute_value.id), ('channel_id.id', '=', self.id)])
            if not mapping_rec:
                woocommerce = self.get_woo_comm_connection()
                woocommerce_attribute_id = self.env['woo.comm.attribute.mapping'].search(
                    [('attribute_id', '=', attribute_value.attribute_id.id), ('channel_id.id', '=', self.id)])
                if woocommerce_attribute_id:
                    attribute_id = woocommerce_attribute_id.woo_comm_attribute_id
                    attribute_value_dict = {
                        "name": attribute_value.name,
                    }
                    return_value_dict = woocommerce.post(
                        'products/attributes/' + str(attribute_id) + "/terms",
                        attribute_value_dict
                    ).json()
                    if 'message' in return_value_dict:
                        raise UserError(_('Error in Creating terms ' + str(return_value_dict['message'])))
                    attr_val += 1
                    mapping_dict = {
                        'channel_id': self.id,
                        'woo_comm_attribute_value_id': return_value_dict['id'],
                        'attribute_value_id': attribute_value.id,
                        'product_attribute_value_id': attribute_value.id,
                        'woo_comm_attribute_value_name': attribute_value.name,
                        'operation': 'export'
                    }
                    obj = self.env['woo.comm.attribute.value.mapping']
                    self._create_mapping(obj, mapping_dict)
                    self._cr.commit()
        return attr_val

    def export_woo_comm_attribute_vals(self):
        attr = 0
        attr_val = 0
        attribute_value_records = ''
        attribute_records = self.env['product.attribute'].search([])
        for attribute in attribute_records:
            mapping_rec = self.env['woo.comm.attribute.mapping'].search(
                [('attribute_id', '=', attribute.id), ('channel_id.id', '=', self.id)])
            if not mapping_rec:
                woocommerce = self.get_woo_comm_connection()
                attribute_dict = {
                    "name": attribute.name,
                    "type": "select",
                    "order_by": "menu_order",
                    "has_archives": True
                }
                return_dict = woocommerce.post('products/attributes',
                                               attribute_dict
                                               ).json()
                attr += 1
                if 'message' in return_dict:
                    raise UserError(_('Error in Creating Attributes   :' + str(return_dict['message'])))
                mapping_dict = {
                    'channel_': self.id,
                    'woo_comm_attribute_id': return_dict['id'],
                    'attribute_id': attribute.id,
                    'product_attribute_id': attribute.id,
                    'woo_comm_attribute_name': attribute.name,
                    'operation': 'export'
                }
                obj = self.env['woo.comm.attribute.mapping']
                self._create_mapping(obj, mapping_dict)
                attribute_value_records = self.env['product.attribute.value'].search(
                    [('attribute_id', '=', attribute.id)]
                )
                for attribute_value in attribute_value_records:
                    mapping_rec = self.env['woo.comm.attribute.value.mapping'].search(
                        [('attribute_value_id', '=', attribute_value.id), ('channel_id.id', '=', self.id)]
                    )
                    if not mapping_rec:
                        attribute_value_dict = {
                            "name": attribute_value.name,
                        }
                        return_value_dict = woocommerce.post('products/attributes/' + str(return_dict['id']) + "/term",
                                                             attribute_value_dict).json()
                        if 'message' in return_value_dict:
                            raise UserError(_('Error in Creating Attributes Terms:' + str(return_dict['message'])))
                        attr_val += 1
                        mapping_dict = {
                            'channel_id': self.id,
                            'woo_comm_attribute_value_id': return_value_dict['id'],
                            'attribute_value_id': attribute_value.id,
                            'product_attribute_value_id': attribute_value.id,
                            'woo_comm_attribute_value_name': attribute_value.name,
                            'operation': 'export'
                        }
                        obj = self.env['woo.comm.attribute.value.mapping']
                        self._create_mapping(obj, mapping_dict)
                        self._cr.commit()
        return attr, attr_val

    def export_woo_comm_attribute_vals_with_id(self, attribute):
        attr = 0
        attr_val = 0
        attribute_value_records = ''
        mapping_rec = self.env['woo.comm.attribute.mapping'].search(
            [('attribute_id', '=', attribute.id), ('channel_id.id', '=', self.id)])
        if not mapping_rec:
            woocommerce = self.get_woo_comm_connection()
            attribute_dict = {
                "name": attribute.name,
                "type": "select",
                "order_by": "menu_order",
                "has_archives": True
            }
            return_dict = woocommerce.post('products/attributes', attribute_dict).json()
            attr += 1
            if 'message' in return_dict:
                raise UserError(_('Error in Creating Attributes   :' + str(return_dict['message'])))
            mapping_dict = {
                'channel_': self.id,
                'woo_comm_attribute_id': return_dict['id'],
                'attribute_id': attribute.id,
                'product_attribute_id': attribute.id,
                'operation': 'export'
            }
            obj = self.env['woo.comm.attribute.mapping']
            self._create_mapping(obj, mapping_dict)
            attribute_value_records = self.env['product.attribute.value'].search(
                [('attribute_id', '=', attribute.id)]
            )
            for attribute_value in attribute_value_records:
                mapping_rec = self.env['woo.comm.attribute.value.mapping'].search(
                    [('attribute_value_id', '=', attribute_value.id), ('channel_id.id', '=', self.id)]
                )
                if not mapping_rec:
                    attribute_value_dict = {"name": attribute_value.name}
                    return_value_dict = woocommerce.post('products/attributes/' + str(return_dict['id']) + "/term",
                                                        attribute_value_dict).json()
                    if 'message' in return_value_dict:
                        raise UserError(_('Error in Creating Attributes Terms   :' + str(return_dict['message'])))
                    attr_val += 1
                    mapping_dict = {
                        'channel_id': self.id,
                        'woo_comm_attribute_value_id': return_value_dict['id'],
                        'attribute_value_id': attribute_value.id,
                        'product_attribute_value_id': attribute_value.id,
                        'operation': 'export'
                    }
                    obj = self.env['woo.comm.attribute.value.mapping']
                    self._create_mapping(obj, mapping_dict)
                    self._cr.commit()
        return attr, attr_val

    def export_woo_comm_attributes_vals(self):
        attribute, value = self.export_woo_comm_attribute_vals()
        value1 = self.export_woo_comm_all_vals()
        value = value + value1
        message = str(attribute) + " Attributes has been exported & " + str(value) + " Attribute Terms have been exported"
        return self.display_message(message)

    def export_woo_comm_all_categ(self):
        message = self.sudo().export_woo_comm_updated_categ()
        count = self.sudo().export_woo_comm_categ(0)
        message += str(count) + " Categories has been exported"
        return self.display_message(message)

    def export_woo_comm_categ(self, count, parent_id=False):
        # self.import_woo_comm_categ()
        parent = 0
        category_records = self.env['product.category'].search([])
        if parent_id:
            category_records = self.env['product.category'].browse(parent_id)
        for category in category_records:
            mapping_rec = self.env['woo.comm.product.category.mapping'].search(
                [('categ_id', '=', category.id), ('channel_id.id', '=', self.id)])
            if mapping_rec and parent_id:
                return mapping_rec.wc_product_categ_id
            if not mapping_rec:
                count = count + 1
                if category.parent_id:
                    parent = self.export_woo_comm_categ(count, category.parent_id.id)
                woocommerce = self.get_woo_comm_connection()
                category_dict = {'name': category.name}
                if parent:
                    category_dict.update({'parent': parent})
                return_dict = woocommerce.post('products/categories', category_dict).json()

                print("return_dict::::::::::::::::::::::::::::::",return_dict)

                # if 'message' in return_dict:
                #     raise UserError(_('Error in Creating Categories : ' + str(return_dict['message'])))

                if 'code' in return_dict:
                    print("return_dict::::::::::::::::::::",return_dict['code'])
                    if str(return_dict['code']) != "term_exists":
                        if str(return_dict['code']) != "missing_parent":
                            mapping_dict = {
                                'channel_id': self.id,
                                'wc_product_categ_id': return_dict['id'],
                                'categ_id': category.id,
                                'product_category_id': category.id,
                                'operation': 'export'
                            }
                            obj = self.env['woo.comm.product.category.mapping']
                            self._create_mapping(obj, mapping_dict)
                            if parent_id:
                                return return_dict['id']
        self._cr.commit()
        return count

    def export_woo_comm_categ_id(self, category):
        parent = False
        if category:
            mapping_rec = self.env['woo.comm.product.category.mapping'].search(
                [('categ_id', '=', category.id), ('channel_id.id', '=', self.id)])
            if not mapping_rec:
                if category.parent_id:
                    parent = self.export_woo_comm_categ(0, category.parent_id.id)
                woocommerce = self.get_woo_comm_connection()
                category_dict = {'name': category.name}
                if parent:
                    category_dict.update({'parent': parent})
                return_dict = woocommerce.post('products/categories', category_dict).json()
                # if 'message' in return_dict:
                #     raise UserError(_('Error Creating Categories : ' + str(return_dict['message'])))
                if 'code' in return_dict:

                    if str(return_dict['code']) != "term_exists":
                        mapping_dict = {
                            'channel_id': self.id,
                            'wc_product_categ_id': return_dict['id'],
                            'categ_id': category.id,
                            'product_category_id': category.id,
                            'operation': 'export'
                        }
                        obj = self.env['woo.comm.product.category.mapping']
                        self._create_mapping(obj, mapping_dict)
                        self._cr.commit()
                        return return_dict['id']
        return False

    def action_export_woo_comm_product(self):
        self.sudo().export_woo_comm_attributes_vals()
        self.sudo().export_woo_comm_categ(0)
        woocommerce = self.get_woo_comm_connection()
        count = 0
        template_ids = []
        if 'active_ids' in self._context:
            if self._context['active_model'] == 'product.template':
                template_ids = self._context['active_ids']
            elif self._context['active_model'] == 'product.product':
                product_records = self.env['product.product'].browse(self._context['active_ids'])
                for product in product_records:
                    template_ids.append(product.product_tmpl_id.id)
            else:
                raise UserError(_('Context Empty'))
        template_records = self.env['product.template'].browse(template_ids)
        for template in template_records:
            mapping_record = self.env['template.mapping'].search(
                [('odoo_template_id', '=', template.id), ('channel_id.id', '=', self.id)])
            if not mapping_record:
                variable = 0
                if len(template.product_variant_ids) > 1:
                    variable = 1
                elif len(template.product_variant_ids) == 1:
                    if template.product_variant_ids[0].product_template_attribute_value_ids:
                        variable = 1
                if variable:
                    count += self.create_woo_comm_product_template(template, woocommerce)
                else:
                    count += self.create_woo_comm_product(template, woocommerce)
        return self.display_message(str(count) + " Products have been exported")

    def set_woo_comm_img_path(self, name, product):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        image_url = '/channel/image/product.product/%s/image_1920/300x300.png' % (product.id)
        full_image_url = '%s' % urlparse.urljoin(base_url, image_url)
        return full_image_url, name

    def create_woo_comm_img_product(self, template, variant=False):
        if template.image_1920:
            image_list = []
            count = 0
            template_url, name = self.set_woo_comm_img_path(template.name, template.product_variant_ids[0])
            image_list.append({
                'src': template_url,
                'name': name,
                'position': 0,
            })
            if variant:
                for variation in template.product_variant_ids:
                    count += 1
                    variant_url, name = self.set_woo_comm_img_path(variation.name + str(count), variation)
                    image_list.append({
                        'src': variant_url,
                        'name': name,
                        'position': count,
                    })
            return image_list

    def get_woo_comm_attribute_dict(self, variant):
        if variant:
            attribute_dict = []
            if variant.product_template_attribute_value_ids:
                for attribute_line in variant.product_template_attribute_value_ids:
                    attr_name, attr_id = self.get_woo_comm_attribute(attribute_line.attribute_id)
                    value_name = attribute_line.name
                    attribute_dict.append({
                        'id': attr_id,
                        'name': attr_name,
                        'option': value_name,
                    })
                return attribute_dict

    def get_woo_comm_attribute_vals(self, attribute_line):
        value_list = []
        if attribute_line:
            for value in attribute_line.value_ids:
                value_list.append(value.name)
        return value_list

    def get_woo_comm_attribute(self, attribute_id):
        if attribute_id:
            record = self.env['woo.comm.attribute.mapping'].search \
                ([('attribute_id', '=', attribute_id.id), ('channel_id.id', '=', self.id)])
            if record:
                return attribute_id.name, record.woo_comm_attribute_id
            else:
                return self.export_woo_comm_attribute_vals_with_id(attribute_id)

    def set_woo_comm_attribute_line(self, template):
        attribute_list = []
        attribute_count = 0
        if template.attribute_line_ids:
            for attribute_line in template.attribute_line_ids:
                attr_name, attr_id = self.get_woo_comm_attribute(attribute_line.attribute_id)
                values = self.get_woo_comm_attribute_vals(attribute_line)
                attribute_dict = {
                    'name': attr_name,
                    'id': attr_id,
                    'variation': True,
                    'visible': True,
                    'position': attribute_count,
                    'options': values,
                }
                attribute_count += 1
                attribute_list.append(attribute_dict)
        return attribute_list

    def create_woo_comm_product_variation(self, woo_product_id, template, woocommerce, image_ids=False):
        count = 0
        if woo_product_id and template:
            for variant in template.product_variant_ids:
                match_record = self.env['product.mapping'].search \
                    ([('product_name', '=', variant.id), ('channel_id.id', '=', self.id)])
                if not match_record:
                    qty = variant._product_available()
                    quantity = qty[variant.id]['qty_available'] - qty[variant.id]['outgoing_qty']
                    variant_data = {
                        'regular_price': str(variant.with_context(pricelist=self.pricelist_name.id).price) or "",
                        'visible': True,
                        'sku': variant.default_code or "",
                        'stock_quantity': quantity,
                        'description': variant.description or "",
                        'price': variant.with_context(pricelist=self.pricelist_name.id).price,
                        'manage_stock': True,
                        'in_stock': True,
                        'attributes': self.get_woo_comm_attribute_dict(variant),
                    }
                    if variant.length or variant.width or variant.height:
                        dimensions = {
                            u'width': str(variant.width) or "",
                            u'length': str(variant.length) or "",
                            u'unit': str(variant.measure_id.name) or "",
                            u'height': str(variant.height) or "",
                        }
                        variant_data['dimensions'] = dimensions
                    if variant.weight:
                        variant_data['weight'] = str(variant.weight) or ""
                    if image_ids:
                        variant_data.update({'image_1920': {'id': image_ids[count]}})
                    if woocommerce:
                       
                        count += 1
                        return_dict = woocommerce.post("products/" + str(woo_product_id) + "/variations", variant_data).json()
                        if 'id' in return_dict:
                            mapping_dict = {
                                'channel_id': self.id,
                                'store_product_id': woo_product_id,
                                'store_variant_id': return_dict['id'],
                                'odoo_template_id': template.id,
                                'product_name': variant.id,
                                'erp_product_id': variant.id,
                                'default_code': variant.default_code or "",
                                'operation': 'export'
                            }
                            obj = self.env['product.mapping']
                            self._create_mapping(obj, mapping_dict)
                        else:
                            raise UserError(_('Error in creating variant'))
            return count
        else:
            raise UserError(_('Error in creating variant'))

    def create_woo_comm_product_template(self, template, woocommerce):
        if template:
            product_dict = {
                'name': template.name,
                'sku': "",
                # 'images': self.create_woo_comm_img_product(template, True),
                'type': 'variable',
                'categories': self.set_woo_comm_product_categ(template),
                'status': 'publish',
                'manage_stock': False,
                'attributes': self.set_woo_comm_attribute_line(template),
                'default_attributes': self.get_woo_comm_attribute_dict(template.product_variant_ids[0]),
                'short_description': template.description_sale or "",
                'description': template.description or "",
            }
            if template.length or template.width or template.height:
                dimensions = {
                    u'width': str(template.width) or "",
                    u'length': str(template.length) or "",
                    u'unit': str(template.measure_id.name) or "",
                    u'height': str(template.height) or "",
                }
                product_dict['dimensions'] = dimensions
            if template.weight:
                product_dict['weight'] = str(template.weight) or ""
            if woocommerce:
                return_dict = woocommerce.post('products', product_dict).json()
                image_ids = []
                if 'images' in return_dict:
                    for image_1920 in return_dict['images']:
                        if image_1920['position'] != 0:
                            image_ids.append(image_1920['id'])
                if 'id' in return_dict:
                    mapping_dict = {
                        'channel_id': self.id,
                        'store_product_id': return_dict['id'],
                        'odoo_template_id': template.id,
                        'template_name': template.id,
                        'default_code': template.default_code or "",
                        'operation': 'export'
                    }
                    obj = self.env['template.mapping']
                    self._create_mapping(obj, mapping_dict)
                    if image_ids:
                        count = self.create_woo_comm_product_variation(return_dict['id'], template, woocommerce, image_ids)
                    else:
                        count = self.create_woo_comm_product_variation(return_dict['id'], template, woocommerce)
                    if count:
                        return count
                else:
                    raise UserError(_("Error in Creating Variable product"))

    def create_woo_comm_product(self, template, woocommerce):
        if template:
            record = self.env['product.product'].search([('product_tmpl_id', '=', template.id)])

            quantity = 0
            if record:
                quantity = record.qty_available            


            # qty = record._product_available()

            # quantity = qty[template.product_variant_ids[0].id]['qty_available'] - \
            #            qty[template.product_variant_ids[0].id]['outgoing_qty']

            product_dict = {
                'name': template.name,
                'sku': template.default_code or "",
                'regular_price': str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
                'type': 'simple',
                'categories': self.set_woo_comm_product_categ(template),
                'status': 'publish',
                'short_description': template.description_sale or "",
                'description': template.description or "",
                'attributes': self.set_woo_comm_attribute_line(template),
                'price': template.with_context(pricelist=self.pricelist_name.id).price,
                'manage_stock': True,
                'stock_quantity': quantity,
                'in_stock': True,
            }

            # if template.image_1920:
            #     product_dict['images'] = self.create_woo_comm_img_product(template)
            if template.length or template.width or template.height:
                dimensions = {
                    u'width': str(template.width) or "",
                    u'length': str(template.length) or "",
                    u'unit': str(template.measure_id.name) or "",
                    u'height': str(template.height) or "",
                }
                product_dict['dimensions'] = dimensions
            if template.weight:
                product_dict['weight'] = str(template.weight)
            if woocommerce:
                return_dict = woocommerce.post('products', product_dict).json()

            if 'id' in return_dict:
                mapping_dict = {
                    'channel_id': self.id,
                    'store_product_id': return_dict['id'],
                    'odoo_template_id': template.id,
                    'template_name': template.id,
                    'default_code': template.default_code or "",
                    'operation': 'export'
                }
                obj = self.env['template.mapping']
                self._create_mapping(obj, mapping_dict)
                mapping_dict = {
                    'channel_id': self.id,
                    'store_product_id': return_dict['id'],
                    'odoo_template_id': template.id,
                    'product_name': template.product_variant_ids[0].id,
                    'erp_product_id': template.product_variant_ids[0].id,
                    'default_code': template.product_variant_ids[0].default_code or "",
                    'operation': 'export'
                }
                obj = self.env['product.mapping']
                self._create_mapping(obj, mapping_dict)
                return 1
            else:
                pass
                # raise UserError(_('Simple Product Creation Failed'))
        # raise UserError(_('Simple Product Creation Failed'))

    def set_woo_comm_product_categ(self, template):
        categ_list = []
        if template.categ_id:
            rec = self.env['woo.comm.product.category.mapping'].search \
                ([('categ_id', '=', template.categ_id.id), ('channel_id.id', '=', self.id)])
            if rec:
                categ_list.append({'id': rec.wc_product_categ_id})
            else:
                cat_id = self.export_woo_comm_categ_id(template.categ_id)
                categ_list.append({'id': cat_id})
        if template.extra_categ_ids:
            for category_channel in template.extra_categ_ids:
                if category_channel.instance_id.id == self.id:
                    for category in category_channel.extra_category_ids:
                        record = self.env['woo.comm.product.category.mapping'].search \
                            ([('categ_id', '=', category.id), ('channel_id.id', '=', self.id)])
                        if record:
                            categ_list.append({'id': record.wc_product_categ_id})
                        else:
                            cat_id = self.export_woo_comm_categ_id(template.categ_id)
                            categ_list.append({'id': cat_id})
        return categ_list

    def export_woo_comm_product(self):
        message = ""
        woocommerce = self.get_woo_comm_connection()
        count = 0
        template_records = self.env['product.template'].search([('type', '=', 'product'), ('sale_ok', '=', True)])
        for template in template_records:
            mapping_record = self.env['template.mapping'].search \
                ([('odoo_template_id', '=', template.id), ('channel_id.id', '=', self.id)])
            if not mapping_record:
                variable = 0
                if len(template.product_variant_ids) > 1:
                    variable = 1
                elif len(template.product_variant_ids) == 1:
                    if template.product_variant_ids[0].product_template_attribute_value_ids:
                        variable = 1
                if variable:
                    prod = self.create_woo_comm_product_template(template, woocommerce)
                    if prod:
                        count += prod
                else:
                    prod = self.create_woo_comm_product(template, woocommerce)
                    if prod:
                        count += prod
        message += str(count) + " Products have been exported"
        return self.display_message(message)

    def export_woo_comm_updated_categ(self):
        count = 0
        wc_product_categ_id = 0
        category_update = self.env['woo.comm.product.category.mapping'].search(
            [('need_sync', '=', 'yes'), ('channel_id.id', '=', self.id)])
        for category_map in category_update:
            category = category_map.product_category_id
            count += 1
            if category.parent_id:
                parent_category = self.env['woo.comm.product.category.mapping'].search(
                    [('categ_id', '=', category.parent_id.id), ('channel_id.id', '=', self.id)])
                if not parent_category:
                    self.export_woo_comm_categ(0)
                    parent_category = self.env['woo.comm.product.category.mapping'].search(
                        [('categ_id', '=', category.parent_id.id), ('channel_id.id', '=', self.id)])
                    wc_product_categ_id = parent_category.wc_product_categ_id
            category_dict = {
                'name': category.name,
                'parent_id': wc_product_categ_id,
            }
            woocommerce = self.get_woo_comm_connection()
            return_dict = woocommerce.put('products/categories/' + category_map.wc_product_categ_id,
                                          category_dict).json()
            if 'message' in return_dict:
                raise UserError(_('Error in Updating Categories:' + str(return_dict['message'])))
            category_map.need_sync = 'no'
        return self.display_message(str(count) + "Categories Updated")

    def export_woo_comm_updated_product(self):
        count = 0
        self.export_woo_comm_categ(0);
        self.export_woo_comm_attribute_vals()
        template_mapping = self.env['template.mapping'].search(
            [('need_sync', '=', 'yes'), ('channel_id.id', '=', self.id)])
        for check in template_mapping:
            count = len(template_mapping)
            template = check.template_name
            store_id = check.store_product_id
            woocommerce = self.get_woo_comm_connection()
            try:
                product_dict = woocommerce.get('products/' + str(store_id)).json()
                if 'bundle_layout' in product_dict:
                    product_dict.pop('bundle_layout')
                if 'message' in product_dict:
                    raise UserError(_("Can't fetch product " + str(product_dict['message'])))
                else:
                    if product_dict['type'] == 'simple':

                        if len(template.product_variant_ids) == 1 and not template.attribute_line_ids:
                            status = self.update_woo_comm_product(template, store_id, product_dict,
                                                                            woocommerce)
                            if status:
                                message = "Products Updated Successfully , "
                        elif len(template.product_variant_ids) == 1 and template.attribute_line_ids and not \
                                template.product_variant_ids[0].product_template_attribute_value_ids:
                            status = self.update_woo_comm_product(template, store_id, product_dict,
                                                                            woocommerce)
                            if status:
                                message = "Products Updated Successfully , "
                        elif len(template.product_variant_ids) >= 1 and template.attribute_line_ids:
                            count = self.update_woo_comm_simple_to_varient_product(template, store_id,
                                                                                    product_dict, woocommerce)
                            if count:
                                message = str(count) + " Variants added, Product's updated Successfully , "
                        else:
                            raise UserError(_('No Variant'))
                    elif product_dict['type'] == 'variable':
                        product_map = self.env['product.mapping'].search(
                            [('odoo_template_id.id', '=', template.id), ('channel_id.id', '=', self.id)])
                        if len(product_map) == len(template.product_variant_ids):
                            status = self.update_woo_comm_varient_product(template, product_map, product_dict,
                                                                              woocommerce)
                            if status:
                                message = "Products Updated!  "
                        else:
                            status = self.create_or_update_woo_comm_varient_product(template, product_map,
                                                                                     product_dict, woocommerce)
                            if status:
                                message = "Products Updated!  "
                    else:
                        raise UserError(_("Product Type Not Supported"))
            except Exception as e:
                raise UserError(_("Can't fetch product" + str(e)))
            check.need_sync = 'no'
        return self.display_message(str(count) + " Products Updated! ")

    def action_woo_comm_updated_product(self):
        template_ids = []
        message = ''
        if 'active_ids' in self._context:
            if self._context['active_model'] == 'product.template':
                template_ids = self._context['active_ids']
            elif self._context['active_model'] == 'product.product':
                product_records = self.env['product.product'].browse(self._context['active_ids'])
                for product in product_records:
                    template_ids.append(product.product_tmpl_id.id)
            else:
                raise UserError(_('Context is Empty'))

            for template_id in template_ids:
                check = self.env['template.mapping'].search(
                    [('odoo_template_id', '=', template_id), ('channel_id.id', '=', self.id)])
                if not check:
                    return self.action_export_woo_comm_product()
                else:
                    template = check.template_name
                    store_id = check.store_product_id
                    woocommerce = self.get_woo_comm_connection()
                    try:
                        product_dict = woocommerce.get('products/' + str(store_id)).json()
                        if 'bundle_layout' in product_dict:
                            product_dict.pop('bundle_layout')
                        if 'message' in product_dict:
                            raise UserError(_("Can't fetch product " + str(product_dict['message'])))
                        else:
                            if product_dict['type'] == 'simple':
                                if len(template.product_variant_ids) == 1 and not template.attribute_line_ids:
                                    status = self.update_woo_comm_product(template, store_id,
                                                                                    product_dict, woocommerce)
                                    if status:
                                        message = "Product Updated Successfully , "
                                elif len(template.product_variant_ids) == 1 and template.attribute_line_ids and not \
                                        template.product_variant_ids[0].product_template_attribute_value_ids:
                                    status = self.update_woo_comm_product(template, store_id,
                                                                                    product_dict, woocommerce)
                                    if status:
                                        message = "Products Updated Successfully , "
                                elif len(template.product_variant_ids) >= 1 and template.attribute_line_ids:
                                    count = self.update_woo_comm_simple_to_varient_product(template, store_id,
                                                                                            product_dict,
                                                                                            woocommerce)
                                    if count:
                                        message = str(count) + " Variants added, Product's updated Successfully , "
                                else:
                                    raise UserError(_('No Variant'))
                            elif product_dict['type'] == 'variable':
                                product_map = self.env['product.mapping'].search(
                                    [('odoo_template_id.id', '=', template.id), ('channel_id.id', '=', self.id)])
                                if len(product_map) == len(template.product_variant_ids):
                                    status = self.update_woo_comm_varient_product(template, product_map,
                                                                                      product_dict, woocommerce)
                                    if status:
                                        message = "Products Updated!  "
                                else:
                                    status = self.create_or_update_woo_comm_varient_product(template, product_map,
                                                                                             product_dict,
                                                                                             woocommerce)
                                    if status:
                                        message = "Products Updated!  "
                            else:
                                raise UserError(_("Product Type Not Supported"))
                    except Exception as e:
                        raise UserError(_("Can't fetch product , " + str(e)))
                check.need_sync = 'no'
            return self.display_message(message)

    def update_woo_comm_product(self, template, store_id, product_dict, woocommerce):
        if woocommerce and template:
            product_dict.update({
                'name': template.name,
                'images': self.create_woo_comm_img_product(template),
                'sku': template.default_code or "",
                'regular_price': str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
                'attributes': self.set_woo_comm_attribute_line(template),
                'categories': self.set_woo_comm_product_categ(template),
                'short_description': template.description_sale or "",
                'description': template.description or "",
                'price': template.with_context(pricelist=self.pricelist_name.id).price,
            })
            if template.length or template.width or template.height:
                dimensions = {
                    u'width': str(template.width) or "",
                    u'length': str(template.length) or "",
                    u'unit': str(template.measure_id.name) or "",
                    u'height': str(template.height) or "",
                }
                product_dict['dimensions'] = dimensions
            if template.weight:
                product_dict['weight'] = str(template.weight) or ""
            try:
                return_dict = woocommerce.put('products/' + str(store_id), product_dict).json()
                if 'message' in return_dict:
                    raise UserError(_("Can't update product ,  " + str(return_dict['message'])))
            except Exception as e:
                raise UserError(_("Can't update product ,  " + str(e)))
        return True

    def update_woo_comm_simple_to_varient_product(self, template, store_id, product_dict, woocommerce):
        count = 0
        if woocommerce and template:
            product_dict.update({
                'name': template.name,
                'images': self.create_woo_comm_img_product(template, True),
                'sku': "",
                'regular_price': str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
                'type': 'variable',
                'attributes': self.set_woo_comm_attribute_line(template),
                'default_attributes': self.get_woo_comm_attribute_dict(template.product_variant_ids[0]),
                'categories': self.set_woo_comm_product_categ(template),
                'short_description': template.description_sale or "",
                'description': template.description or "",
                'price': template.with_context(pricelist=self.pricelist_name.id).price,
            })
            if template.length or template.width or template.height:
                dimensions = {
                    u'width': str(template.width) or "",
                    u'length': str(template.length) or "",
                    u'unit': str(template.measure_id.name) or "",
                    u'height': str(template.height) or "",
                }
                product_dict['dimensions'] = dimensions
            if template.weight:
                product_dict['weight'] = str(template.weight) or ""
            try:
                return_dict = woocommerce.put('products/' + str(store_id), product_dict).json()
                unlink_record = self.env['product.mapping'].search \
                    ([('odoo_template_id.id', '=', template.id), ('channel_id.id', '=', self.id)])
                unlink_record.unlink()
                if 'message' in return_dict:
                    raise UserError(_("Can't update product's from simple to variable " + str(return_dict['message'])))
                else:
                    image_ids = []
                    for image_1920 in return_dict['images']:
                        if image_1920['position'] != 0:
                            image_ids.append(image_1920['id'])
                    if image_ids:
                        count = self.create_woo_comm_product_variation(return_dict['id'], template, woocommerce, image_ids)
                    else:
                        count = self.create_woo_comm_product_variation(return_dict['id'], template, woocommerce)
                    if count:
                        return count
            except Exception as e:
                raise UserError(_("Can't update product from simple to variable"))

    def update_woo_comm_varient_product(self, template, product_map, product_dict, woocommerce):
        if woocommerce and template:
            product_dict.update({
                'name': template.name,
                'images': self.create_woo_comm_img_product(template, True),
                'sku': "",
                'regular_price': str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
                'type': 'variable',
                'attributes': self.set_woo_comm_attribute_line(template),
                'default_attributes': self.get_woo_comm_attribute_dict(template.product_variant_ids[0]),
                'categories': self.set_woo_comm_product_categ(template),
                'short_description': template.description_sale or "",
                'description': template.description or "",
                'price': template.with_context(pricelist=self.pricelist_name.id).price,
            })
            if template.length or template.width or template.height:
                dimensions = {
                    u'width': str(template.width) or "",
                    u'length': str(template.length) or "",
                    u'unit': str(template.measure_id.name) or "",
                    u'height': str(template.height) or "",
                }
                product_dict['dimensions'] = dimensions
            if template.weight:
                product_dict['weight'] = str(template.weight) or ""
            try:
                return_dict = woocommerce.put('products/' + str(product_dict['id']), product_dict).json()
                if 'message' in return_dict:
                    raise UserError(_("Can't update product from simple to variable :  " + str(return_dict['message'])))
                else:
                    image_ids = []
                    for image_1920 in return_dict['images']:
                        if image_1920['position'] != 0:
                            image_ids.append(image_1920['id'])
                    if image_ids:
                        count = self.update_woo_comm_varient(return_dict['id'], template, product_map
                                                                  , woocommerce, image_ids)
                    else:
                        count = self.update_woo_comm_varient(return_dict['id'], template, product_map
                                                                  , woocommerce)
                    if count:
                        return count
            except Exception as e:
                raise UserError(_("Can't update  variable product  " + str(e)))

    def update_woo_comm_varient(self, store_product_id, template, product_map, woocommerce, image_ids=False):
        count = 0
        if store_product_id and woocommerce and product_map:
            for product in product_map:
                store_variant_id = product.store_variant_id
                variant = product.product_name
                variant_data = {
                    'regular_price': str(variant.with_context(pricelist=self.pricelist_name.id).price) or "",
                    'visible': True,
                    'sku': variant.default_code or "",
                    'description': variant.description or "",
                    'price': variant.with_context(pricelist=self.pricelist_name.id).price,
                    'attributes': self.get_woo_comm_attribute_dict(variant),
                }
                if variant.length or variant.width or variant.height:
                    dimensions = {
                        u'width': str(variant.width) or "",
                        u'length': str(variant.length) or "",
                        u'unit': str(variant.measure_id.name) or "",
                        u'height': str(variant.height) or "",
                    }
                    variant_data['dimensions'] = dimensions
                if variant.weight:
                    variant_data['weight'] = str(variant.weight) or ""
                if image_ids:
                    variant_data.update({'image_1920': {'id': image_ids[count]}})
                if woocommerce:
                    try:
                        return_dict = woocommerce.put \
                            ("products/" + str(store_product_id) + "/variations/" + str(store_variant_id)
                             , variant_data).json()
                        if 'message' in return_dict:
                            raise UserError(_("Can't Update variant  " + str(return_dict['message'])))
                        count += 1
                    except Exception as e:
                        raise UserError(_("Can't Update variant  " + str(e)))
            return count

    def create_or_update_woo_comm_varient_product(self, template, product_map, product_dict, woocommerce):
        if woocommerce and template:
            product_dict.update({
                'name': template.name,
                'images': self.create_woo_comm_img_product(template, True),
                'sku': "",
                'regular_price': str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
                'type': 'variable',
                'attributes': self.set_woo_comm_attribute_line(template),
                'default_attributes': self.get_woo_comm_attribute_dict(template.product_variant_ids[0]),
                'categories': self.set_woo_comm_product_categ(template),
                'short_description': template.description_sale or "",
                'description': template.description or "",
                'price': template.with_context(pricelist=self.pricelist_name.id).price,
            })
            if template.length or template.width or template.height:
                dimensions = {
                    u'width': str(template.width) or "",
                    u'length': str(template.length) or "",
                    u'unit': str(template.measure_id.name) or "",
                    u'height': str(template.height) or "",
                }
                product_dict['dimensions'] = dimensions
            if template.weight:
                product_dict['weight'] = str(template.weight) or ""
            try:
                return_dict = woocommerce.put('products/' + str(product_dict['id']), product_dict).json()
                if 'message' in return_dict:
                    raise UserError(_("Can't update product from simple to variable " + str(return_dict['message'])))
                else:
                    image_ids = []
                    for image_1920 in return_dict['images']:
                        if image_1920['position'] != 0:
                            image_ids.append(image_1920['id'])
                    if image_ids:
                        count = self.update_woo_comm_varient(return_dict['id'], template, product_map
                                                                  , woocommerce, image_ids)
                    else:
                        count = self.update_woo_comm_varient(return_dict['id'], template, product_map
                                                                  , woocommerce)
                    if count:
                        if image_ids:
                            self.create_woo_comm_extra_variation(return_dict['id'], template, woocommerce, count,
                                                                    image_ids)
                        else:
                            self.create_woo_comm_extra_variation(return_dict['id'], template, woocommerce, count)
                    return count
            except Exception as e:
                raise UserError(_("Can't update product from simple to variable"))

    def create_woo_comm_extra_variation(self, store_product_id, template, woocommerce, count, image_ids=False):
        if store_product_id and woocommerce:
            if store_product_id and template:
                for variant in template.product_variant_ids:
                    match_record = self.env['product.mapping'].search \
                        ([('erp_product_id', '=', variant.id), ('channel_id.id', '=', self.id)])
                    if not match_record:
                        qty = variant._product_available()
                        quantity = qty[variant.id]['qty_available'] - qty[variant.id]['outgoing_qty']
                        variant_data = {
                            'regular_price': str(variant.with_context(pricelist=self.pricelist_name.id).price) or "",
                            'visible': True,
                            'sku': variant.default_code or "",
                            'stock_quantity': quantity,
                            'description': variant.description or "",
                            'price': variant.with_context(pricelist=self.pricelist_name.id).price,
                            'manage_stock': True,
                            'in_stock': True,
                            'attributes': self.get_woo_comm_attribute_dict(variant),
                        }
                        if variant.length or variant.width or variant.height:
                            dimensions = {
                                u'width': str(variant.width) or "",
                                u'length': str(variant.length) or "",
                                u'unit': str(variant.measure_id.name) or "",
                                u'height': str(variant.height) or "",
                            }
                            variant_data['dimensions'] = dimensions
                        if variant.weight:
                            variant_data['weight'] = str(variant.weight) or ""
                        if image_ids:
                            variant_data.update({'image_1920': {'id': image_ids[count]}})
                        if woocommerce:
                            try:
                                return_dict = woocommerce.post("products/" + str(store_product_id) + "/variations"
                                                               , variant_data).json()
                                if 'message' in return_dict:
                                    raise UserError("Error in Updation and Creation of variant during update " + str
                                    (return_dict['message']))
                                count += 1
                            except Exception as e:
                                raise UserError("Error in Updation and Creation of variant during update " + str(e))
                            if 'id' in return_dict:
                                mapping_dict = {
                                    'channel_id': self.id,
                                    'store_product_id': store_product_id,
                                    'store_variant_id': return_dict['id'],
                                    'odoo_template_id': template.id,
                                    'product_name': variant.id,
                                    'erp_product_id': variant.id,
                                    'default_code': variant.default_code or "",
                                    'operation': 'export'
                                }
                                obj = self.env['product.mapping']
                                self._create_mapping(obj, mapping_dict)
                            else:
                                raise UserError(_('Error in creating variant :  ' + str(return_dict['message'])))
                return count
            else:
                raise UserError(_('Error in creating variant'))

    def import_woo_comm_categ(self):
        message = ''
        woocommerce = self.get_woo_comm_connection()
        if self.id:
            category_map_data = self.env['woo.comm.product.category.mapping']
            count = 0
            i = 1
            while(i):
                cat_url = 'products/categories'
                category_data = woocommerce.get(cat_url, params={"page": i}).json()
                if category_data:
                    count += self.import_woo_comm_all_categ(cat_url)
                    i += 1
                else:
                    i = 0
            message += str(count) + " Categories Imported!"
            return self.display_message(message)

    def import_woo_comm_all_categ(self, cat_url, parent_id=False):
        message = ''
        list_category = []
        category_map_data = self.env['woo.comm.product.category.mapping']
        count = 0
        woocommerce = self.get_woo_comm_connection()
        if not cat_url and parent_id:
            cat_url = 'products/categories'
            cat_url = cat_url + "/" + str(parent_id)
        category_data = woocommerce.get(cat_url,params={'per_page': 100}).json()

        if isinstance(category_data, dict):
            if category_data.get('message'):
                raise UserError(_("Error : ") + category_data.get('message'))
            category_data = [category_data, ]

        for category in category_data:                
            if category['parent'] and not category_map_data.search(
                    [('wc_product_categ_id', '=', category['parent']), ('channel_id.id', '=', self.id)]):
                self.import_woo_comm_all_categ(False, category['parent'])
            if not category_map_data.search(
                    [('wc_product_categ_id', '=', category['id']), ('channel_id.id', '=', self.id)]) and not self.env[
                'category.feed'].search([('store_id', '=', category['id']), ('channel_id.id', '=', self.id)]):
                category_search_record = self.env['product.category'].search(
                    [('name', '=', category['name']), ('extra_categ_ids.instance_id.id', '=', self.id)])
                if category_search_record:
                    mapping_dict = {
                        'channel_id': self.id,
                        'wc_product_categ_id': category['id'],
                        'categ_id': category_search_record.id,
                        'product_category_id': category_search_record.id,
                    }
                    obj = self.env['woo.comm.product.category.mapping']
                    self._create_mapping(obj, mapping_dict)
                else:
                    count = count + 1
                    category_dict = {
                        'name': category['name'],
                        'parent_id': category['parent'] or '',
                        'store_id': category['id'],
                        'channel_id': self.id,
                    }
                    category_rec = self.env['category.feed'].create(category_dict)
                    self._cr.commit()
                    list_category.append(category_rec)
        feed_res = dict(create_ids=list_category, update_ids=[])
        self.env['channel.operation'].post_feed_import_process(self, feed_res)
        self._cr.commit()
        return count

    def create_or_update_woo_comm_voucher(self, vouchers):
        voucher_rec = self.env['product.feed'].search([('name', '=', 'voucher')])
        if not voucher_rec:
            voucher_rec = self.create_woo_comm_voucher()
        voucher_list = []
        for voucher in vouchers:
            voucher_line = {
                'line_name': "Voucher",
                'line_price_unit': -(float(voucher['amount'])),
                'line_product_uom_qty': 1,
                'line_product_id': voucher_rec.store_id,
                'line_source': 'discount'
            }
            voucher_list.append((0, 0, voucher_line))
        return voucher_list

    def create_woo_comm_voucher(self):
        data = {
            'name': "voucher",
            'store_id': "wc",
            'channel_id': self.id,
            'type': 'service'
        }
        product_rec = self.env['product.feed'].create(data)
        feed_res = dict(create_ids=[product_rec], update_ids=[])
        self.env['channel.operation'].post_feed_import_process(self, feed_res)
        return product_rec

    def create_or_update_woo_comm_shipping(self, shipping_line):
        shipping_rec = self.env['product.feed'].search([('name', '=', 'shipping')])
        if not shipping_rec:
            shipping_rec = self.create_woo_comm_shipping()
        shipping_list = []
        for shipping in shipping_line:
            if float(shipping['total']) > 0:
                tax = self.get_woo_comm_account_tax(shipping['taxes'])
                shipping_line = {
                    'line_name': "Shipping",
                    'line_price_unit': float(shipping['total']),
                    'line_product_uom_qty': 1,
                    'line_product_id': shipping_rec.store_id,
                    'line_taxes': tax,
                    'line_source': 'delivery',
                }
                shipping_list.append((0, 0, shipping_line))
        return shipping_list

    def create_woo_comm_shipping(self):
        data = {
            'name': "shipping",
            'store_id': "sh",
            'channel_id': self.id,
            'type': 'service'
        }
        product_rec = self.env['product.feed'].create(data)
        feed_res = dict(create_ids=[product_rec], update_ids=[])
        self.env['channel.operation'].post_feed_import_process(self, feed_res)
        return product_rec

    def get_woo_comm_account_tax(self, data):
        list = []
        if data:
            for taxes in data:
                if 'total' in taxes:
                    if taxes['total']:
                        if float(taxes['total']) > 0:
                            list.append({'id': taxes['id']})
        return list

    def get_woo_comm_sale_orderline(self, data):
        order_lines = []
        for line in data:
            if not self.env['template.mapping'].search(
                    [('store_product_id', '=', line['product_id']), ('channel_id.id', '=', self.id)]):
                self.import_woo_comm_product_id(line['product_id'])
            product_template_id = self.env['product.mapping'].search(
                [('store_variant_id', '=', line['variation_id']), ('channel_id.id', '=', self.id)])
            if not product_template_id:
                product_template_id = self.env['product.mapping'].search(
                    [('store_product_id', '=', line['product_id']), ('channel_id.id', '=', self.id)])
            order_line_dict = {
                'line_name': line['name'],
                'line_price_unit': line['price'],
                'line_product_uom_qty': line['quantity'],
                'line_product_id': product_template_id.store_product_id,
                'line_variant_ids': product_template_id.store_variant_id,
                'line_taxes': self.get_woo_comm_account_tax(line['taxes'])
            }
            order_lines.append((0, 0, order_line_dict))
        return order_lines

    def import_woo_comm_sale_orders(self):
        self.import_woo_comm_attribute()
        # self.import_woo_comm_categ()

        woocommerce = self.get_woo_comm_connection()
        message = ''
        self.create_or_check_woo_comm_tax(woocommerce)
        list_order = []
        count = 0
        context = dict(self._context)
        order_feed_data = self.env['order.feed']
        date = self.with_context({'name': 'order'}).get_import_date()
        if not date:
            raise UserError(_("Please set date in multi channel configuration"))
        try:
            i = 1
            while(i):
                order_data = woocommerce.get('orders?page=' + str(i) + '&after=' + date).json()
                if 'errors' in order_data:
                    raise UserError(_("Error : " + str(order_data['errors'][0]['message'])))
                else:
                    if order_data:
                        i = i + 1
                        for order in order_data:
                            _logger.info("===============================>%r", order['id'])
                            if not order_feed_data.search(
                                    [('store_id', '=', order['id']), ('channel_id.id', '=', self.id)]):
                                count = count + 1
                                if order['id']:
                                    woocommerce2 = woocommerce
                                    if woocommerce2:
                                        order_data = woocommerce2.get("orders/" + str(order['id'])).json()
                                        data = order_data['line_items']
                                        order_lines = self.get_woo_comm_sale_orderline(data)
                                        if order['shipping_lines']:
                                            order_lines += self.create_or_update_woo_comm_shipping(
                                                order_data['shipping_lines'])
                                customer = {}
                                if order['customer_id']:
                                    customer = woocommerce.get('customers/' + str(order['customer_id'])).json()
                                else:
                                    customer.update({'first_name': order['billing']['first_name'],
                                                     'last_name': order['billing']['last_name'],
                                                     'email': order['billing']['email']})
                                method_title = 'Delivery'
                                if order['shipping_lines']:
                                    method_title = order['shipping_lines'][0]['method_title']
                                order_dict = {
                                    'store_id': order['id'],
                                    'channel_id': self.id,
                                    'partner_id': order['customer_id'] or order['billing']['email'],
                                    'payment_method': order['payment_method_title'],
                                    'line_type': 'multi',
                                    'carrier_id': method_title,
                                    'line_ids': order_lines,
                                    'currency': order['currency'],
                                    'customer_name': customer['first_name'] + " " + customer['last_name'],
                                    'customer_email': customer['email'],
                                    'order_state': order['status'],
                                }
                                if order['billing']:
                                    order_dict.update({
                                        'invoice_partner_id': order['billing']['email'],
                                        'invoice_name': order['billing']['first_name'] + " " + order['billing'][
                                            'last_name'],
                                        'invoice_email': order['billing']['email'],
                                        'invoice_phone': order['billing']['phone'],
                                        'invoice_street': order['billing']['address_1'],
                                        'invoice_street2': order['billing']['address_2'],
                                        'invoice_zip': order['billing']['postcode'],
                                        'invoice_city': order['billing']['city'],
                                        'invoice_state_id': order['billing']['state'],
                                        'invoice_country_id': order['billing']['country'],
                                    })
                                if order['shipping']:
                                    order_dict['same_shipping_billing'] = False
                                    order_dict.update({
                                        'shipping_partner_id': order['billing']['email'],
                                        'shipping_name': order['shipping']['first_name'] + " " + order['billing'][
                                            'last_name'],
                                        'shipping_street': order['shipping']['address_1'],
                                        'shipping_street2': order['shipping']['address_2'],
                                        'shipping_email': order['billing']['email'],
                                        'shipping_zip': order['shipping']['postcode'],
                                        'shipping_city': order['shipping']['city'],
                                        'shipping_state_id': order['shipping']['state'],
                                        'shipping_country_id': order['shipping']['country'],
                                    })
                                order_rec = order_feed_data.with_context(context).create(order_dict)
                                self._cr.commit()
                                list_order.append(order_rec)
                    else:
                        i = 0
            context.update({'group_by': 'state'})
            list_order.reverse()
            feed_res = dict(create_ids=list_order, update_ids=[])
            self.env['channel.operation'].with_context(context).post_feed_import_process(self, feed_res)
            self.import_order_date = str(datetime.now().date())
            message += str(count) + " Order(s) Imported!"
            return self.display_message(message)
        except Exception as e:
            raise UserError(_("Error : " + str(e)))

    def import_woo_comm_all_sale_orders(self):
        self.import_woo_comm_attribute()
        # self.import_woo_comm_categ()
        woocommerce = self.get_woo_comm_connection()
        message = ''
        self.create_or_check_woo_comm_tax(woocommerce)
        list_order = []
        count = 0
        context = dict(self._context)
        order_feed_data = self.env['order.feed']
        try:
            i = 1
            while (i):
                order_data = woocommerce.get('orders', params={'page': i}).json()
                if 'errors' in order_data:
                    raise UserError(_("Error : " + str(order_data['errors'][0]['message'])))
                else:
                    if order_data:
                        i = i + 1
                        for order in order_data:
                            _logger.info("===============================>%r", order['id'])
                            if not order_feed_data.search(
                                    [('store_id', '=', order['id']), ('channel_id.id', '=', self.id)]):
                                count = count + 1
                                if order['id']:
                                    woocommerce2 = woocommerce
                                    if woocommerce2:
                                        order_data = woocommerce2.get("orders/" + str(order['id'])).json()
                                        data = order_data['line_items']
                                        order_lines = self.get_woo_comm_sale_orderline(data)
                                        if order['shipping_lines']:
                                            order_lines += self.create_or_update_woo_comm_shipping(
                                                order_data['shipping_lines'])
                                customer = {}
                                if order['customer_id']:
                                    customer = woocommerce.get('customers/' + str(order['customer_id'])).json()
                                else:
                                    customer.update({'first_name': order['billing']['first_name'],
                                                     'last_name': order['billing']['last_name'],
                                                     'email': order['billing']['email']})
                                _logger.info("===================>%r", [order['billing'], order['shipping'], order])

                                method_title = 'Delivery'
                                if order['shipping_lines']:
                                    method_title = order['shipping_lines'][0]['method_title']
                                customer_vat = "CF"
                                meta_data = order.get('meta_data', False)
                                _logger.info('*******************meta_data*************************')
                                _logger.info(meta_data)
                                _logger.info('*******************order_dict*************************')
                                _logger.info(order)
                                if order.get('meta_data', False):
                                    for line in order.get('meta_data', []):
                                        if line.get('key', False) and line.get('key') == '_billing_wooccm11':
                                            customer_vat = line.get('value')
                                order_dict = {
                                    'store_id': order['id'],
                                    'channel_id': self.id,
                                    'partner_id': order['customer_id'] or order['billing']['email'],
                                    'payment_method': order['payment_method_title'],
                                    'line_type': 'multi',
                                    'carrier_id': method_title,
                                    'line_ids': order_lines,
                                    'currency': order['currency'],
                                    'customer_name': customer['first_name'] + " " + customer['last_name'],
                                    'customer_email': customer['email'],
                                    #'customer_vat': customer_vat,
                                    'order_state': order['status'],
                                }
                                if order['billing']:
                                    order_dict.update({
                                        'invoice_partner_id': order['billing']['email'],
                                        'invoice_name': order['billing']['first_name'] + " " + order['billing'][
                                            'last_name'],
                                        'invoice_email': order['billing']['email'],
                                        'invoice_phone': order['billing']['phone'],
                                        'invoice_street': order['billing']['address_1'],
                                        'invoice_street2': order['billing']['address_2'],
                                        'invoice_zip': order['billing']['postcode'],
                                        'invoice_city': order['billing']['city'],
                                        'invoice_state_id': order['billing']['state'],
                                        'invoice_country_id': order['billing']['country'],
                                    })
                                if order['shipping']:
                                    order_dict['same_shipping_billing'] = False
                                    order_dict.update({
                                        'shipping_partner_id': order['billing']['email'],
                                        'shipping_name': order['shipping']['first_name'] + " " + order['billing']['last_name'],
                                        'shipping_street': order['shipping']['address_1'],
                                        'shipping_street2': order['shipping']['address_2'],
                                        'shipping_email': order['billing']['email'],
                                        'shipping_zip': order['shipping']['postcode'],
                                        'shipping_city': order['shipping']['city'],
                                        'shipping_state_id': order['shipping']['state'],
                                        'shipping_country_id': order['shipping']['country'],
                                    })
                                order_rec = order_feed_data.with_context(context).create(order_dict)
                                self._cr.commit()
                                list_order.append(order_rec)
                    else:
                        i = 0
            context.update({'group_by': 'state'})
            list_order.reverse()
            feed_res = dict(create_ids=list_order, update_ids=[])
            self.env['channel.operation'].with_context(context).post_feed_import_process(self, feed_res)
            self.import_order_date = str(datetime.now().date())
            message += str(count) + " Order(s) Imported!"
            return self.display_message(message)
        except Exception as e:
            raise UserError(_("Error : " + str(e)))

    def import_woo_comm_res_partner(self):
        message = ''
        list_customer = []
        count = 0
        woocommerce = self.get_woo_comm_connection()
        partner_feed_data = self.env['partner.feed']
        date = self.with_context({'name': 'customer'}).get_import_date()
        if not date:
            return self.display_message("Please set date in multi channel configuration")
        try:
            partner_data = woocommerce.get('customers', params={"after": date}).json()

        except Exception as e:
            raise UserError(_("Error : " + str(e)))
        if 'message' in partner_data:
            raise UserError(_("Error : " + str(partner_data['message'])))
        else:
            for partner in partner_data:
                if not partner_feed_data.search([('store_id', '=', partner['id']), ('channel_id.id', '=', self.id)]):
                    count = count + 1
                    partner_dict = {
                        'name': partner['first_name'],
                        'last_name': partner['last_name'],
                        'channel_id': self.id,
                        'email': partner['email'],
                        'store_id': partner['id'],
                    }
                    partner_rec = partner_feed_data.create(partner_dict)
                    self._cr.commit()
                    list_customer.append(partner_rec)
            feed_res = dict(create_ids=list_customer, update_ids=[])
            self.env['channel.operation'].post_feed_import_process(self, feed_res)
            self.import_customer_date = str(datetime.now().date())
            message += str(count) + " Customer(s) Imported!"
            return self.display_message(message)

    def import_woo_comm_all_res_partner(self):
        message = ''
        list_customer = []
        count = 0
        woocommerce = self.get_woo_comm_connection()
        partner_feed_data = self.env['partner.feed']
        try:
            i = 1
            while(i):
                partner_data = woocommerce.get('customers', params={"page": i}).json()
                if 'message' in partner_data:
                    raise UserError(_("Error : " + str(partner_data['message'])))
                else:
                    if partner_data:
                        i = i + 1
                        for partner in partner_data:
                            if not partner_feed_data.search([('store_id', '=', partner['id']), ('channel_id.id', '=', self.id)]):
                                count = count + 1
                                partner_dict = {
                                    'name': partner['first_name'],
                                    'last_name': partner['last_name'],
                                    'channel_id': self.id,
                                    'email': partner['email'],
                                    'store_id': partner['id'],
                                }
                                partner_rec = partner_feed_data.create(partner_dict)
                                self._cr.commit()
                                list_customer.append(partner_rec)
                    else:
                        i = 0
            feed_res = dict(create_ids=list_customer, update_ids=[])
            self.env['channel.operation'].post_feed_import_process(self, feed_res)
            message += str(count) + " Customer(s) Imported!"
            return self.display_message(message)
        except Exception as e:
            raise UserError(_("Error : " + str(e)))

    def create_woo_comm_product_varients(self, woocommerce, product_id):
        variant_list = []
        attribute_list = []
        varient_image = False
        product_feed_id = self.env['product.feed'].search([('store_id','=',product_id)],limit=1)
        product_template_ids = self.env['product.template'].search([('name','=',product_feed_id.name)],limit=1)
        # for variant_id in variation_ids:
        variant = woocommerce.get('products/' + str(product_id) ).json()
        # variant = woocommerce.get('products/' + str(product_id) + "/variations/" + str(variant_id)).json()
        if variant['attributes']:
            attribute_list = []
            for attributes in variant['attributes']:
                attrib_name_id = self.env['woo.comm.attribute.mapping'].search(
                    [('woo_comm_attribute_name', '=', attributes['name']), ('channel_id.id', '=', self.id)])
                attrib_value_id = self.env['woo.comm.attribute.value.mapping'].search(
                    [('woo_comm_attribute_value_name', 'in', attributes['options']), ('channel_id.id', '=', self.id),
                     ('product_attribute_value_id.attribute_id.id', '=', attrib_name_id.product_attribute_id.id)])

                attr = {}
                attr['name'] = str(attributes['name'])
                attr['value'] = str(attributes['options'])
                attr['attrib_name_id'] = attrib_name_id.woo_comm_attribute_id

                for attr_val in attrib_value_id:
                    attr['attrib_value_id'] = attr_val.woo_comm_attribute_value_id
                attribute_list.append(attr)



                # if isinstance(variant['image'], list):
                #     if len(variant['image']) > 0:
                #         product_image_url = variant['image'][0]['src']
                #     else:
                #         product_image_url = ''
                #     varient_image = product_image_url
                # else:
                #     if variant['image'] == None:
                #         varient_image = ''

            if product_template_ids:
                for i in attribute_list:
                    product_attribute = self.env['product.attribute'].search([('name', 'ilike', i['name'])])

                    if not product_attribute:
                        product_attribute = self.env['product.attribute'].create({
                            'name': i['name'],
                        })
                        # ['green']
                    attribute_value = str(i['value'])[1:-1]
                    attribute_value.split(',')
                    lst = []
                    lst.append(attribute_value)
                    value_attr = eval(i['value'])
                    lst_attr_value = []
                    for value_attribute in value_attr:
                        product_attribute_value = self.env['product.attribute.value'].search(
                            [('attribute_id', '=', product_attribute.id), ('name', '=',value_attribute)])
                        lst_attr_value.append(product_attribute_value.id)
                        if not product_attribute_value:
                            product_attribute_value = self.env['product.attribute.value'].create({
                                'name': i['value'],
                                'attribute_id': product_attribute.id,
                            })
                    if product_attribute.id:
                        if product_attribute.id not in product_template_ids.attribute_line_ids.attribute_id.ids:
                            product_template_ids.write({
                                'attribute_line_ids': [
                                    (0, 0, {
                                        'attribute_id': product_attribute.id,
                                        'value_ids': [(6, 0, lst_attr_value)],
                                    }),
                                ]
                            })
                        else:
                            for l in product_template_ids.attribute_line_ids:
                                if l.attribute_id.id == product_attribute.id:
                                    l.value_ids = lst_attr_value


        try:
            variant['price'] = float(variant['price'])
        except:
            pass
        variant_dict = {
            'image_url': varient_image,
            'name_value': attribute_list,
            'store_id': variant['id'],
            'default_code': variant['sku'],
            'list_price': variant['price'],
            'qty_available': variant['stock_quantity'],
            'weight': variant['weight'] or "",
            'length': variant['dimensions']['length'] or "",
            'width': variant['dimensions']['width'] or "",
            'height': variant['dimensions']['height'] or "",
        }

        variant_list.append((0, 0, variant_dict))
        return variant_list

    def import_woo_comm_attribute(self, woocommerce=False):
        attribute_list = []
        attribute_id = 0
        if not woocommerce:
            woocommerce = self.get_woo_comm_connection()
        i = 1
        while (i):
            try:
                attribute_data = woocommerce.get('products/attributes', params={'page': i}).json()
            except Exception as e:
                raise UserError(_("Error : " + str(e)))
            if 'message' in attribute_data:
                raise UserError(_("Error : " + str(attribute_data['message'])))
            else:
                if attribute_data:
                    i = i + 1
                    for attribute in attribute_data:
                        attribute_map = self.env['woo.comm.attribute.mapping'].search(
                            [('woo_comm_attribute_id', '=', attribute['id']), ('channel_id.id', '=', self.id)])
                        if not attribute_map:
                            product_attributes_obj = self.env['product.attribute']
                            attribute_search_record = product_attributes_obj.search(
                                ['|', ('name', '=', attribute['name'].lower()), '|',
                                 ('name', '=', attribute['name'].title()), ('name', '=', attribute['name'].upper())])
                            if not attribute_search_record:
                                attribute_id = product_attributes_obj.create({'name': attribute['name']})
                            else:
                                attribute_id = attribute_search_record
                            attribute_list.append({'id': attribute['id'], 'value': attribute_id.id})
                            mapping_dict = {
                                'channel_id': self.id,
                                'woo_comm_attribute_id': attribute['id'],
                                'woo_comm_attribute_name': attribute['name'],
                                'attribute_id': attribute_id.id,
                                'product_attribute_id': attribute_id.id,
                            }
                            obj = self.env['woo.comm.attribute.mapping']
                            self._create_mapping(obj, mapping_dict)
                            self._cr.commit()
                    else:
                        i = 0
            attr_term = self.import_woo_comm_attribute_list(attribute_list, woocommerce)
            self._cr.commit()
            if attr_term:
                return woocommerce
            else:
                return False

    def import_woo_comm_attribute_list(self, attribute_list=False, woocommerce=False):
        if not woocommerce:
            woocommerce = self.get_woo_comm_connection()
        attribute_value_id = 0
        for attribute in attribute_list:
            i = 1
            while (i):
                try:
                    attribute_term_data = woocommerce.get(
                        'products/attributes/' + str(attribute['id']) + '/terms', params={"page": i}).json()
                except Exception as e:
                    raise UserError(_("Error : " + str(e)))
                if 'message' in attribute_term_data:
                    raise UserError(_("Error : " + str(attribute_term_data['message'])))
                else:
                    if attribute_term_data:
                        i = i + 1
                        for term in attribute_term_data:
                            term_map = self.env['woo.comm.attribute.value.mapping'].search(
                                [('woo_comm_attribute_value_id', '=', term['id']), ('channel_id.id', '=', self.id)])
                            if not term_map:
                                product_attributes_value_obj = self.env['product.attribute.value']
                                attribute_value_search_record = product_attributes_value_obj.search([
                                    ('attribute_id', '=', attribute['value']),
                                    '|', ('name', '=', term['name'].lower()),
                                    '|', ('name', '=', term['name'].title()),
                                    ('name', '=', term['name'].upper())
                                ])
                                if not attribute_value_search_record:
                                    attribute_value_id = product_attributes_value_obj.create(
                                        {'name': term['name'], 'attribute_id': attribute['value']})
                                else:
                                    attribute_value_id = attribute_value_search_record
                                mapping_dict = {
                                    'channel_id': self.id,
                                    'woo_comm_attribute_value_id': term['id'],
                                    'woo_comm_attribute_value_name': term['name'],
                                    'attribute_value_id': attribute_value_id.id,
                                    'product_attribute_value_id': attribute_value_id.id,
                                    'store_selection': 'woocommerce',
                                }
                                obj = self.env['woo.comm.attribute.value.mapping']
                                self._create_mapping(obj, mapping_dict)
                                self._cr.commit()
                    else:
                        i = 0
        return True

    def import_woo_comm_products(self):
        woocommerce = False
        message = ''
        woo_instance = self.import_woo_comm_attribute()
        if not woo_instance:
            raise UserError("Failed To Create Attribute Values")
        else:
            woocommerce = woo_instance
        if not woocommerce:
            woocommerce = self.get_woo_comm_connection()
        self.import_woo_comm_categ()
        count = 0
        list_product = []
        product = ''
        product_tmpl = self.env['product.feed']
        date = self.with_context({'name': 'product'}).get_import_date()
        if not date:
            raise UserError(_("Date required in multi channel configuration"))
        try:
            i = 1
            while (i):
                product_data = woocommerce.get('products?after=' + date, params={"page": i}).json()
                # product_data = woocommerce.get('products?after=' + date + '&page=' + str(i)).json()
                if 'errors' in product_data:
                    raise UserError(_("Error : " + str(product_data['errors'][0]['message'])))
                else:
                    if product_data:
                        i = i + 1
                        for product in product_data:
                            variants = []
                            if not self.env['template.mapping'].search(
                                    [('store_product_id', '=', product['id']), ('channel_id.id', '=', self.id)]):
                                categ = ""
                                if product['type'] == 'variable':
                                    variants = self.create_woo_comm_product_varients(woocommerce, product['id'])
                                count = count + 1
                                for category in product['categories']:
                                    category_id = self.env['woo.comm.product.category.mapping'].search(
                                        [('wc_product_categ_id', '=', category['id']), ('channel_id.id', '=', self.id)])
                                    if category_id:
                                        categ = categ + str(category_id.wc_product_categ_id) + ","
                                try:
                                    product['price'] = float(product['price'])
                                except:
                                    pass
                                if len(product['images']) > 0:
                                    product_image_url = product['images'][0]['src']
                                else:
                                    product_image_url = ''
                                product_feed_dict = {'name': product['name'],
                                                     'store_id': product['id'],
                                                     'default_code': product['sku'],
                                                     'list_price': product['price'],
                                                     'channel_id': self.id,
                                                     'description_sale': remove_tag.sub('', product['description']),
                                                     'qty_available': product['stock_quantity'],
                                                     'feed_variants': variants,
                                                     'image_url': product_image_url,
                                                     'multi_image_url_ids': multi_image_url_ids,
                                                     'extra_categ_ids': categ or '',
                                                     }
                                if not product['type'] == 'variable':
                                    product_feed_dict.update({
                                        'weight': product['weight'] or "",
                                        'length': product['dimensions']['length'] or "",
                                        'width': product['dimensions']['width'] or "",
                                        'height': product['dimensions']['height'] or "",
                                    })
                                if product['downloadable'] == True or product['virtual'] == True:
                                    product_feed_dict.update({'type': 'service'})
                                product_rec = product_tmpl.create(product_feed_dict)

                                # multi image
                                if product_rec:
                                    url_list = []
                                    for url in product['images']:
                                        url_list.append((0,0, {
                                            'product_feed_id':product_rec.id,
                                            'multi_image_url':url['src'],
                                        }))
                                    product_rec.multi_image_url_ids = url_list


                                self._cr.commit()
                                list_product.append(product_rec)
                    else:
                        i = 0

            feed_res = dict(create_ids=list_product, update_ids=[])
            self.env['channel.operation'].post_feed_import_process(self, feed_res)
            self.import_product_date = str(datetime.now().date())
            message += str(count) + " Product(s) Imported!"
            return self.display_message(message)
        except Exception as e:
            raise UserError(_("Error  :  " + str(e)))

    def import_woo_comm_all_product(self):
        woocommerce = False
        message = ''
        woo_instance = self.import_woo_comm_attribute()
        if not woo_instance:
            raise UserError("Failed To Create Attribute Values")
        else:
            woocommerce = woo_instance
        if not woocommerce:
            woocommerce = self.get_woo_comm_connection()
        # self.import_woo_comm_categ()
        list_product = []
        count = 0
        product_tmpl = self.env['product.feed']
        try:
            i = 1
            while (i):
                try:
                    product_data = woocommerce.get('products', params={"page": i}).json()
                except Exception as e:
                    raise UserError(_("Error : " + str(e)))
                # if product_data == []:
                #     return True
                if 'errors' in product_data:
                    raise UserError(_("Error : " + str(product_data['errors'][0]['message'])))
                else:
                    if product_data:
                        i = i + 1
                        for product in product_data:
                            variants = []
                            if not self.env['template.mapping'].search(
                                    [('store_product_id', '=', product['id']), ('channel_id.id', '=', self.id)]):
                                categ = ""
                                if product['type'] == 'variable':
                                    variants = self.create_woo_comm_product_varients(woocommerce, product['id'])
                                count = count + 1
                                for category in product['categories']:
                                    category_id = self.env['category.feed'].search(
                                        [('name', '=', category), ('channel_id.id', '=', self.id)])

                                    if category_id:
                                        categ = categ + str(category_id.store_id) + ","
                                try:
                                    product['price'] = float(product['price'])
                                except:
                                    pass
                                if len(product['images']) > 0:
                                    product_image_url = product['images'][0]['src']
                                else :
                                    product_image_url = ''
                                product_feed_dict = {'name': product['name'],
                                                     'store_id': product['id'],
                                                     'default_code': product['sku'],
                                                     'list_price': product['price'],
                                                     'channel_id': self.id,
                                                     'description_sale': remove_tag.sub('', product['description']),
                                                     'qty_available': product['stock_quantity'],
                                                     'feed_variants': variants,
                                                     'image_url': product_image_url,
                                                     'extra_categ_ids': categ,
                                                     'store_selection': 'woocommerce',
                                                     }
                                if not product['type'] == 'variable':
                                    product_feed_dict.update({
                                        'weight': product['weight'] or "",
                                        'length': product['dimensions']['length'] or "",
                                        'width': product['dimensions']['width'] or "",
                                        'height': product['dimensions']['height'] or "",
                                    })
                                if product['downloadable'] == True or product['virtual'] == True:
                                    product_feed_dict.update({'type': 'service'})
                                product_rec = product_tmpl.create(product_feed_dict)

                                # multi image
                                if product_rec:
                                    url_list = []
                                    for url in product['images']:
                                        url_list.append((0,0, {
                                            'product_feed_id':product_rec.id,
                                            'multi_image_url':url['src'],
                                        }))
                                    product_rec.multi_image_url_ids = url_list

                                self._cr.commit()
                                list_product.append(product_rec)
                    else:
                        i = 0
            feed_res = dict(create_ids=list_product, update_ids=[])
            self.env['channel.operation'].post_feed_import_process(self, feed_res)
            message += str(count) + " Product(s) Imported!"
            return self.display_message(message)
        except Exception as e:
            raise UserError(_("Error:" + str(e)))

    def import_woo_comm_product_id(self, id):
        message = ''
        woocommerce = self.get_woo_comm_connection()
        list_product = []
        product = ''
        product_tmpl = self.env['product.feed']
        try:
            product = woocommerce.get('products/' + str(id)).json()
        except Exception as e:
            raise UserError(_("1 Error : " + str(e)))
        # if 'message' in product:
        #     raise UserError(_("2 Error : " + str(product['message'])))
        if 'message' not in product:
            variants = []
            if not self.env['template.mapping'].search(
                    [('store_product_id', '=', product['id']), ('channel_id.id', '=', self.id)]):
                categ = ""
                if product['type'] == 'variable':
                    variants = self.create_woo_comm_product_varients(woocommerce, product['id'])
                for category in product['categories']:
                    category_id = self.env['category.feed'].search(
                        [('name', '=', category), ('channel_id.id', '=', self.id)])
                    if category_id:
                        categ = categ + str(category_id.store_id) + ","
                try:
                    product['price'] = float(product['price'])
                except:
                    pass
                if len(product['images']) > 0:
                    product_image_url = product['images'][0]['src']
                else:
                    product_image_url = ''
                product_feed_dict = {'name': product['name'],
                                     'store_id': product['id'],
                                     'default_code': product['sku'],
                                     'list_price': product['price'],
                                     'channel_id': self.id,
                                     'description_sale': remove_tag.sub('', product['description']),
                                     'qty_available': product['stock_quantity'],
                                     'feed_variants': variants,
                                     'image_url': product_image_url,
                                     'extra_categ_ids': categ,
                                     'store_selection': 'woocommerce',
                                     }
                if product['downloadable'] == True or product['virtual'] == True:
                    product_feed_dict['type'] = 'service'
                if not product['type'] == 'variable':
                    product_feed_dict.update({
                        'weight': product['weight'] or "",
                        'length': product['dimensions']['length'] or "",
                        'width': product['dimensions']['width'] or "",
                        'height': product['dimensions']['height'] or "",
                    })
                product_rec = product_tmpl.create(product_feed_dict)

                # multi image
                if product_rec:
                    url_list = []
                    for url in product['images']:
                        url_list.append((0,0, {
                            'product_feed_id':product_rec.id,
                            'multi_image_url':url['src'],
                        }))
                    product_rec.multi_image_url_ids = url_list

                self._cr.commit()
                list_product.append(product_rec)
            feed_res = dict(create_ids=list_product, update_ids=[])
            self.env['channel.operation'].post_feed_import_process(self, feed_res)
            return True

    def create_or_check_woo_comm_tax(self, woocommerce):
        if woocommerce:
            i = 1
            while (i):
                try:
                    taxes = woocommerce.get("taxes", params={"page": i}).json()
                except Exception as e:
                    raise UserError(_("Error : " + str(e)))
                if 'message' in taxes:
                    raise UserError(_("Error : " + str(taxes['message'])))
                else:
                    if taxes:
                        i += 1
                        tax_obj = self.env['account.tax']
                        tax_map_obj = self.env['woo.comm.account.mapping']
                        tax_list = []
                        domain = []
                        channel = str(self.channel)
                        for tax in taxes:
                            check = tax_map_obj.search(
                                [('store_id', '=', int(tax['id'])), ('channel_id.id', '=', self.id)])
                            tax_srch = tax_obj.search([('name', '=', tax['name'])])
                            tax_rate = float(tax['rate'])
                            if not check:
                                if tax_srch:
                                    tax_map_vals = {
                                        'channel_id': self.id,
                                        'account_tax_id': tax_srch.id,
                                        'wc_tax_id': tax_srch.amount,
                                        'tax_type': tax_srch.amount_type,
                                        'is_tax_include_in_price': tax_srch.price_include,
                                        'tax_id': tax_srch.id,
                                        'store_id': tax['id'],
                                    }
                                    self._create_mapping(tax_map_obj, tax_map_vals)
                                else:
                                    tax_dict = {
                                        'name': tax['name'],
                                        'amount_type': 'percent',
                                        'price_include': False,
                                        'amount': tax_rate,
                                    }
                                    tax_rec = tax_obj.create(tax_dict)
                                    tax_map_vals = {
                                        'channel_id': self.id,
                                        'account_tax_id': tax_rec.id,
                                        'wc_tax_id': tax_rec.amount,
                                        'tax_type': tax_rec.amount_type,
                                        'is_tax_include_in_price': tax_rec.price_include,
                                        'tax_id': tax_rec.id,
                                        'store_id': tax['id'],
                                    }
                                    self._create_mapping(tax_map_obj, tax_map_vals)

                            else:
                                amount = check.account_tax_id.amount
                                name = check.account_tax_id.name
                                if (name != tax['name'] or amount != tax_rate):
                                    check.account_tax_id.amount = tax_rate
                                    check.account_tax_id.name = tax['name']
                    else:
                        i = 0

        return True

    def update_woo_comm_categ(self):
        update_rec = []
        create_rec = []
        count = 0
        woocommerce = self.get_woo_comm_connection()
        category_feed_data = self.env['category.feed']
        records = self.env['woo.comm.product.category.mapping'].search([('channel_id.id', '=', self.id)])
        i = 0
        id_string = []
        idstr = ''
        for record in records:
            idstr += str(record.wc_product_categ_id) + ','
            i += 1
            if i == 11:
                id_string.append(idstr)
                i = 0
                idstr = ''
        if idstr not in id_string:
            id_string.append(idstr)
        for id_str in id_string:
            try:
                category_data = woocommerce.get('products/categories?include=' + id_str).json()
            except Exception as e:
                raise UserError(_("Error : " + str(e)))
            if 'errors' in category_data:
                raise UserError(_("Error : " + str(category_data['errors'][0]['message'])))
            else:
                for category in category_data:
                    update_record = category_feed_data.search(
                        [('store_id', '=', category['id']), ('channel_id.id', '=', self.id)])
                    if update_record:
                        count += 1
                        update_record.state = 'update'
                        category_dict = {
                            'name': category['name'],
                            'parent_id': category['parent'] or '',
                        }
                        update_record.write(category_dict)
                        update_rec.append(update_record)
                    else:
                        count = count + 1
                        category_dict = {
                            'name': category['name'],
                            'parent_id': category['parent'] or '',
                            'store_id': category['id'],
                            'channel_id': self.id,
                        }
                        category_rec = self.env['category.feed'].create(category_dict)
                        self._cr.commit()
                        update_rec.append(category_rec)
        feed_res = dict(create_ids=create_rec, update_ids=update_rec)
        self.env['channel.operation'].post_feed_import_process(self, feed_res)
        message = str(count) + " Categories Updated!  "
        return self.display_message(message)

    def update_woo_comm_res_partner(self):
        update_rec = []
        count = 0
        woocommerce = self.get_woo_comm_connection()
        partner_feed_data = self.env['partner.feed']
        records = self.env['partner.mapping'].search([('type', '=', 'contact'), ('channel_id.id', '=', self.id)])
        id_string = []
        idstr = ''
        i = 0
        for record in records:
            idstr += str(record.store_customer_id) + ','
            i += 1
            if i == 10:
                id_string.append(idstr)
                i = 0
                idstr = ''
        if idstr not in id_string:
            id_string.append(idstr)
        for id_str in id_string:
            try:
                partner_data = woocommerce.get('customers?include=' + id_str).json()
                _logger.info('********************partner data*******************')
                _logger.info(partner_data)
            except Exception as e:
                raise UserError(_("Error : " + str(e)))
            if 'message' in partner_data:
                raise UserError(_("Error : " + str(partner_data['message'])))
            else:
                for partner in partner_data:
                    update_record = self.env['partner.feed'].search(
                        [('store_id', '=', partner['id']), ('type', '=', 'contact'), ('channel_id.id', '=', self.id)])
                    if update_record:
                        count += 1
                        update_record.state = 'update'
                        partner_dict = {
                            'name': partner['first_name'],
                            'last_name': partner['last_name'],
                            'channel_id': self.id,
                            'email': partner['email'],
                            'store_id': partner['id']
                        }
                        update_record.write(partner_dict)
                        update_rec.append(update_record)
                    else:
                        count = count + 1
                        partner_dict = {
                            'name': partner['first_name'],
                            'last_name': partner['last_name'],
                            'channel_id': self.id,
                            'email': partner['email'],
                            'store_id': partner['id'],
                        }
                        partner_rec = partner_feed_data.create(partner_dict)
                        partner_rec.state = 'update'
                        self._cr.commit()
                        update_rec.append(partner_rec)
        feed_res = dict(create_ids=[], update_ids=update_rec)
        self.env['channel.operation'].post_feed_import_process(self, feed_res)
        self.update_product_date = str(datetime.now().date())
        message = str(count) + "Customers(s) Updated!"
        return self.display_message(message)

    def update_woo_comm_sale_order(self, woocommerce=False):
        update_rec = []
        count = 0
        if not woocommerce:
            woocommerce = self.get_woo_comm_connection()
        order_feed_data = self.env['order.feed']
        records = self.env['order.mapping'].search([('channel_id.id', '=', self.id)])
        id_string = []
        idstr = ''
        i = 0
        for record in records:
            idstr += str(record.store_order_id) + ','
            i += 1
            if i == 10:
                id_string.append(idstr)
                i = 0
                idstr = ''
        if idstr not in id_string:
            id_string.append(idstr)
        for id_str in id_string:
            try:
                order_data = woocommerce.get('orders?include=' + id_str).json()
            except Exception as e:
                raise UserError(_("Error : " + str(e)))
            if 'message' in order_data:
                raise UserError(_("Error : " + str(order_data['message'])))
            else:
                for order in order_data:
                    update_record = self.env['order.feed'].search(
                        [('store_id', '=', order['id']), ('channel_id.id', '=', self.id)])
                    if update_record and update_record.order_state != order['status']:
                        count += 1
                        update_record.state = 'update'
                        order_dict = {
                            'order_state': order['status']
                        }
                        update_record.write(order_dict)
                        update_rec.append(update_record)
        feed_res = dict(create_ids=[], update_ids=update_rec)
        self.env['channel.operation'].post_feed_import_process(self, feed_res)
        self.update_order_date = str(datetime.now().date())
        message = str(count) + " Order(s) Updated!  "
        return self.display_message(message)

    def update_woo_comm_products(self, woocommerce=False):
        update_rec = []
        categ = ''
        count = 0
        if not woocommerce:
            woocommerce = self.get_woo_comm_connection()
        product_tmpl = self.env['product.feed']
        records = self.env['template.mapping'].search([('channel_id.id', '=', self.id)])
        id_string = []
        idstr = ''
        i = 0
        for record in records:
            idstr += str(record.store_product_id) + ','
            i += 1
            if i == 10:
                id_string.append(idstr)
                i = 0
                idstr = ''
        if idstr not in id_string:
            id_string.append(idstr)
        for id_str in id_string:
            try:
                product_data = woocommerce.get('products?include=' + id_str).json()
            except Exception as e:
                raise UserError(_("Error : " + str(e)))
            if 'message' in product_data:
                raise UserError(_("Error : " + str(product_data['message'])))
            else:
                for product in product_data:
                    _logger.info("========test===2===========>%r", [product['id']])
                    variants = []
                    update_record = product_tmpl.search(
                        [('store_id', '=', product['id']), ('channel_id.id', '=', self.id)])
                    if update_record:
                        count += 1
                        update_record.state = 'update'
                        # if product['type'] == 'variable':
                        update_record.write({'feed_variants': [(5,), ]})
                        variants = self.create_woo_comm_product_varients(woocommerce, product['id'])
                        for category in product['categories']:
                            category_id = self.env['category.feed'].search(
                                [('name', '=', category), ('channel_id.id', '=', self.id)])
                            if category_id:
                                categ = categ + str(category_id.store_id) + ","
                        try:
                            product['price'] = float(product['price'])
                        except:
                            pass
                        if len(product['images']) > 0:
                            product_image_url = product['images'][0]['src']
                            url_list = []
                            for url in product['images']:
                                url_list.append((0,0, {
                                    'product_feed_id':update_record.id,
                                    'multi_image_url':url['src'],
                                }))
                            multi_image_url_ids = url_list
                        else:
                            product_image_url = ''
                            multi_image_url_ids = False
                        product_feed_dict = {'name': product['name'],
                                             'store_id': product['id'],
                                             'default_code': product['sku'],
                                             'list_price': product['price'],
                                             'channel_id': self.id,
                                             'description_sale': remove_tag.sub('', product['description']),
                                             'feed_variants': variants,
                                             'image_url': product_image_url,
                                             'multi_image_url_ids': multi_image_url_ids,
                                             'extra_categ_ids': categ,
                                             'weight': product['weight'] or "",
                                             'length': product['dimensions']['length'] or "",
                                             'width': product['dimensions']['width'] or "",
                                             'height': product['dimensions']['height'] or "",
                                             }
                        update_record.write(product_feed_dict)

                        self._cr.commit()
                        update_rec.append(update_record)
                    else:
                        # if product['downloadable'] == True or product['virtual'] == True:
                        #     product_feed_dict['type'] = 'service'
                        if product['type'] == 'variable':
                            variants = self.create_woo_comm_product_varients(woocommerce, product['id'])
                        count = count + 1
                        for category in product['categories']:
                            category_id = self.env['category.feed'].search(
                                [('name', '=', category), ('channel_id.id', '=', self.id)])
                            if category_id:
                                categ = categ + str(category_id.store_id) + ","
                        try:
                            product['price'] = float(product['price'])
                        except:
                            pass
                        if len(product['images']) > 0:
                            product_image_url = product['images'][0]['src']

                            url_list = []
                            for url in product['images']:
                                url_list.append((0,0, {
                                    'product_feed_id':update_record.id,
                                    'multi_image_url':url['src'],
                                }))
                            multi_image_url_ids = url_list
                        else:
                            product_image_url = ''
                            multi_image_url_ids = False
                        product_feed_dict = {'name': product['name'],
                                             'store_id': product['id'],
                                             'default_code': product['sku'],
                                             'list_price': product['price'],
                                             'channel': self.id,
                                             'description_sale': remove_tag.sub('', product['description']),
                                             'feed_variants': variants,
                                             'image_url': product_image_url,
                                             'multi_image_url_ids': multi_image_url_ids,
                                             'extra_categ_ids': categ,
                                             # 'store_select': 'woocommerce',
                                             'weight': product['weight'] or "",
                                             'length': product['dimensions']['length'] or "",
                                             'width': product['dimensions']['width'] or "",
                                             'height': product['dimensions']['height'] or "",
                                             }
                        product_rec = product_tmpl.create(product_feed_dict)
                        product_rec.state = 'update'
                        self._cr.commit()
                        update_rec.append(product_rec)
        feed_res = dict(create_ids=[], update_ids=update_rec)
        self.env['channel.operation'].post_feed_import_process(self, feed_res)
        # self.update_product_date = datetime.now()
        message = str(count) + "Product(s) Updated!"
        return self.display_message(message)
