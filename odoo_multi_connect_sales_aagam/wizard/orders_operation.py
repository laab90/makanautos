# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class Importorders(models.TransientModel):
    _inherit = ['import.operation']
    _name = "import.orders"

    source = fields.Selection(
        [
            ('all', 'All'),
            ('order_ids', 'Order ID(s)'),
        ],
        required=1,
        default='all'
    )

    order_ids = fields.Text('Order ID(s)')


class ExportOrders(models.TransientModel):
    _inherit = ['export.operation']
    _name = "export.orders"


    @api.model
    def default_get(self,fields):
        res = super(ExportOrders,self).default_get(fields)
        if not res.get('order_ids') and self._context.get('active_model') == 'sale.order':
            res['order_ids']=self._context.get('active_ids')
        return res

    order_ids = fields.Many2many('sale.order',string= 'Sale order')
