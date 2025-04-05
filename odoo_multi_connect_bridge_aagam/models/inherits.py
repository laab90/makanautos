# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def cancel_woo_comm_invoice(self):
        context = self.env.context.copy()
        channel_id = self.channel_mapping_ids.channel_id
        if not channel_id:
            error_message = 'Wocommerce Connection needs one Active Configuration setting.'
            status = 'no'
        else:
            con = channel_id.get_woo_comm_connection()
            if con:
                order_id = self.channel_mapping_ids.store_order_id
                #order_status = \
                #self.order_state_ids.filtered(lambda order_state: order_state.odoo_order_state == 'cancelled')[0]
                if order_id:
                    for order in order_id:
                        try:
                            order_data = con.get('orders/'+ str(order)).json()
                        except Exception as e:
                            raise UserError(_("Error: Getting Order %s") + str(e))
                        order_data.update({
                            'status': "cancelled"
                        })
                        try:
                            state_update = con.put('orders/' + str(order), order_data)
                        except Exception as e:
                            raise UserError(_("Error Updating Order Status (Cancelled) %s") % (str(e)))
                else:
                    return True

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        config_id = self.channel_mapping_ids.channel_id
        if 'ecommerce' not in self._context:
            if config_id and config_id.channel == "woocommerce":
                self.cancel_woo_comm_invoice()
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        status = super(ProductTemplate, self).write(vals)
        for product_tmpl in self:
            if product_tmpl.channel_mapping_ids:
                for channel in product_tmpl.channel_mapping_ids:
                    channel.need_sync = 'yes'
        return status


class ProductProduct(models.Model):
    _inherit = "product.product"

    def write(self, vals):
        status = super(ProductProduct, self).write(vals)
        for product in self:
            template = product.product_tmpl_id
            if template.channel_mapping_ids:
                for channel in template.channel_mapping_ids:
                    channel.need_sync = 'yes'
        return status


class ProductCategory(models.Model):
    _inherit = "product.category"

    def write(self, vals):
        status = super(ProductCategory, self).write(vals)
        for product_categ in self:
            if product_categ.channel_mapping_ids:
                for channel in product_categ.channel_mapping_ids:
                    channel.need_sync = 'yes'
        return status


class StockMove(models.Model):
    _inherit = 'stock.move'

    def multichannel_sync_quantity(self, pick_details):
        channel_obj = self.env['woo.comm.channel.sale']
        for channel in pick_details['channel_sale_ids']:
            channel_rec = channel_obj.browse(channel)
            if channel_rec.channel == 'woocommerce' and channel_rec.auto_sync_stock:
                product_record = channel_rec.env['product.mapping'].search(
                    [('erp_product_id', '=', pick_details['product_id']), ('channel_id.id', '=', channel_rec.id)])
                if product_record:
                    woocommerce = channel_rec.get_woo_comm_connection()
                    if channel_rec.location_id.id != pick_details['source_loc_id']:
                        channel_rec.update_woo_comm_qty(woocommerce, pick_details['product_qty'],
                                                                product_record)
                    else:
                        channel_rec.update_woo_comm_qty(woocommerce, -(pick_details['product_qty']),
                                                                product_record)
        # return super(StockMove, self).multichannel_sync_quantity(pick_details)
