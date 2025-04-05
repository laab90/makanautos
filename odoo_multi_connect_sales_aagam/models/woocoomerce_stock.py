# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        """    
        channel_sale_ids = self.env['woo.comm.channel.sale'].search([]).ids
        todo = [move.id for move in self if move.state == "draft"]
        ids = self
        i=0
        if todo:
            ids = self.action_confirm(todo)
        for data in ids:
            erp_product_id = data.product_id.id
            flag = 1
            if (data.origin != False) and data.picking_type_id.code not in ['incoming']:
                sale_id = self.env['sale.order'].search([('name', '=', data.origin)])
                if sale_id:
                    channel_id = sale_id.channel_mapping_ids.channel_id
                    if channel_id and channel_id.id in channel_sale_ids:
                        channel_sale_ids.remove(channel_id.id)
                    flag = 0
            else:
                flag = 2

            if flag == 1:
                if data.picking_type_id:
                    check_pos = self.env['ir.model'].search([('model', '=', 'pos.order')])
                    if check_pos:
                        pos_order_data = self.env['pos.order'].search(
                            [('name', '=', data.origin)])
                        if pos_order_data:
                            lines = pos_order_data[0].lines
                            for line in lines:
                                get_line_data = self.env['pos.order.line'].search(
                                    [('product_id', '=', erp_product_id), ('id', '=', line.id)])
                                if get_line_data:
                                    data.product_qty = get_line_data[0].qty
            if channel_sale_ids:
                pick_details = {
                    'product_id' :  erp_product_id,
                    'location_dest_id' : data.location_dest_id.id,
                    'product_qty' :  data.product_qty,
                    'channel_sale_ids' :  channel_sale_ids,
                    'source_loc_id' : data.location_id.id,
                }
                self.multichannel_sync_quantity(pick_details)
        """
        return res

